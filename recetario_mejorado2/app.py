from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import firebase_admin
from firebase_admin import credentials, firestore
from fpdf import FPDF
import tempfile
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key')  # Reemplaza con una clave secreta mas segura

# Inicializar Firebase
cred = credentials.Certificate('C://recetarioM//recetariommm-firebase-adminsdk-52uq9-43f66a4185.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agregar_doctor', methods=['GET', 'POST'])
def agregar_doctor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        especialidad = request.form['especialidad']
        
        if not nombre or not especialidad:
            flash("Por favor complete todos los campos", "error")
            return redirect(url_for('agregar_doctor'))

        try:
            db.collection('doctores').add({'nombre': nombre, 'especialidad': especialidad})
            flash("Doctor agregado correctamente", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error al agregar el doctor: {e}", "error")
            return redirect(url_for('agregar_doctor'))

    return render_template('agregar_doctor.html')

@app.route('/crear_receta', methods=['GET', 'POST'])
def crear_receta():
    if request.method == 'POST':
        paciente_nombre = request.form['paciente_nombre']
        doctor_nombre = request.form['doctor_nombre']
        detalles = request.form['detalles']
        medicamento_nombre = request.form['medicamento_nombre']
        cantidad = request.form['cantidad']

        try:
            receta_data = {
                'paciente': paciente_nombre,
                'doctor': doctor_nombre,
                'detalles': detalles,
                'medicamento': medicamento_nombre,
                'cantidad': cantidad
            }

            db.collection('recetas').add(receta_data)
            flash("Receta creada correctamente", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error al guardar la receta: {e}", "error")
            return redirect(url_for('crear_receta'))

    return render_template('crear_receta.html')

@app.route('/ver_recetas', methods=['GET'])
def ver_recetas():
    # Recuperamos las recetas desde Firestore
    recetas_ref = db.collection('recetas').stream()
    recetas = [{'id': receta.id, 
                'paciente': receta.to_dict()['paciente'],
                'doctor': receta.to_dict()['doctor'],
                'detalles': receta.to_dict()['detalles'],
                'medicamento': receta.to_dict()['medicamento'],
                'cantidad': receta.to_dict()['cantidad']} for receta in recetas_ref]

    return render_template('ver_recetas.html', recetas=recetas)

@app.route('/generar_pdf/<receta_id>', methods=['GET'])
def generar_pdf(receta_id):
    # Buscar la receta en la base de datos usando receta_id
    receta_ref = db.collection('recetas').document(receta_id).get()
    if not receta_ref.exists:
        return "Receta no encontrada", 404

    receta = receta_ref.to_dict()

    # Crear el PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Establecer la fuente del PDF
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(200, 10, txt="Receta Medica", ln=True, align='C')

    # Agregar la informacion de la receta al PDF
    pdf.ln(10)  # Añadir un salto de línea
    pdf.cell(0, 10, f"Paciente: {receta['paciente']}", ln=True)
    pdf.cell(0, 10, f"Doctor: {receta['doctor']}", ln=True)
    pdf.cell(0, 10, f"Medicamento: {receta['medicamento']}", ln=True)
    pdf.cell(0, 10, f"Cantidad: {receta['cantidad']}", ln=True)
    pdf.cell(0, 10, f"Detalles: {receta['detalles']}", ln=True)

    # Crear un archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        # Guardamos el PDF en el archivo temporal
        pdf.output(temp_file.name)
        
        # Cerramos el archivo temporal, pero Flask manejará el archivo directamente
        temp_file.close()

        # Enviar el archivo PDF al navegador usando send_file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name="receta.pdf",
            mimetype="application/pdf"
        )

# Configuración de la app para correr en el puerto y host deseados
if __name__ == '__main__':
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
