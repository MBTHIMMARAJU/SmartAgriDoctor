from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import random
from datetime import datetime

app = Flask(__name__)

# Configuration - Using SQLite instead of MySQL
app.config['SECRET_KEY'] = 'smartagridoctor-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartagridoctor.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Disease classes for demo
DISEASE_CLASSES = [
    'Apple___Apple_scab', 'Apple___Black_rot', 'Apple___Cedar_apple_rust', 'Apple___healthy',
    'Blueberry___healthy', 'Cherry___Powdery_mildew', 'Cherry___healthy',
    'Corn___Cercospora_leaf_spot', 'Corn___Common_rust', 'Corn___Northern_Leaf_Blight', 'Corn___healthy',
    'Grape___Black_rot', 'Grape___Esca', 'Grape___Leaf_blight', 'Grape___healthy',
    'Orange___Haunglongbing', 'Peach___Bacterial_spot', 'Peach___healthy',
    'Pepper_bell___Bacterial_spot', 'Pepper_bell___healthy', 'Potato___Early_blight', 'Potato___Late_blight', 'Potato___healthy',
    'Raspberry___healthy', 'Soybean___healthy', 'Squash___Powdery_mildew',
    'Strawberry___Leaf_scorch', 'Strawberry___healthy', 'Tomato___Bacterial_spot', 'Tomato___Early_blight',
    'Tomato___Late_blight', 'Tomato___Leaf_Mold', 'Tomato___Septoria_leaf_spot', 'Tomato___Spider_mites',
    'Tomato___Target_Spot', 'Tomato___Tomato_Yellow_Leaf_Curl_Virus', 'Tomato___Tomato_mosaic_virus', 'Tomato___healthy'
]

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

class DetectionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(255))
    predicted_disease = db.Column(db.String(255))
    confidence = db.Column(db.Float)
    detection_time = db.Column(db.DateTime, default=datetime.utcnow)
    treatment_recommendation = db.Column(db.Text)

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    response = db.Column(db.Text)
    language = db.Column(db.String(10), default='en')
    message_time = db.Column(db.DateTime, default=datetime.utcnow)

class PestRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(255), unique=True)
    organic_treatment = db.Column(db.Text)
    chemical_treatment = db.Column(db.Text)
    preventive_measures = db.Column(db.Text)
    suitable_crops = db.Column(db.Text)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Simple disease prediction model (no TensorFlow needed)
class SimpleDiseaseModel:
    def predict_disease(self, image_path):
        """Simulate disease prediction - returns random results for demo"""
        predicted_class = random.randint(0, len(DISEASE_CLASSES) - 1)
        confidence = round(random.uniform(0.7, 0.95), 2)
        return predicted_class, confidence

# Initialize the simple model
disease_model = SimpleDiseaseModel()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('❌ Username already exists.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('❌ Email already exists.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, phone=phone, password_hash=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('✅ Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            # Log login session
            new_session = UserSession(
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(new_session)
            db.session.commit()
            
            flash('✅ Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('❌ Login failed. Check your credentials.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Update logout time in session log
    latest_session = UserSession.query.filter_by(
        user_id=current_user.id, 
        logout_time=None
    ).order_by(UserSession.login_time.desc()).first()
    
    if latest_session:
        latest_session.logout_time = datetime.utcnow()
        db.session.commit()
    
    logout_user()
    flash('ℹ️ You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user detection history
    history = DetectionHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(DetectionHistory.detection_time.desc()).limit(5).all()
    
    return render_template('dashboard.html', history=history)

# ⭐ ONLY ONE disease-detection route ⭐
@app.route('/disease-detection', methods=['GET', 'POST'])
@login_required
def disease_detection():
    # Handle file upload (existing functionality)
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Predict disease
                predicted_class, confidence = disease_model.predict_disease(filepath)
                disease_name = DISEASE_CLASSES[predicted_class]
                
                # Get treatment recommendations
                treatment = get_treatment_recommendation(disease_name)
                
                # Save to database
                new_detection = DetectionHistory(
                    user_id=current_user.id,
                    image_path=filename,
                    predicted_disease=disease_name,
                    confidence=float(confidence),
                    treatment_recommendation=treatment
                )
                db.session.add(new_detection)
                db.session.commit()
                
                return render_template('disease_detection.html', 
                                    prediction=disease_name,
                                    confidence=confidence,
                                    treatment=treatment,
                                    image_url=url_for('static', filename='uploads/' + filename))
            
            except Exception as e:
                flash(f'❌ Error processing image: {str(e)}', 'danger')
    
    # Check if this is a camera result redirect
    camera_result = request.args.get('camera_result')
    if camera_result:
        # Get the latest detection for this user
        latest_detection = DetectionHistory.query.filter_by(
            user_id=current_user.id
        ).order_by(DetectionHistory.detection_time.desc()).first()
        
        if latest_detection:
            return render_template('disease_detection.html', 
                                prediction=latest_detection.predicted_disease,
                                confidence=latest_detection.confidence,
                                treatment=latest_detection.treatment_recommendation,
                                image_url=url_for('static', filename='uploads/' + latest_detection.image_path))
    
    return render_template('disease_detection.html')

# ⭐ NEW camera route ⭐
@app.route('/take-photo', methods=['POST'])
@login_required
def take_photo():
    """Handle photo taken from camera"""
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo data'}), 400
    
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'error': 'No photo selected'}), 400
    
    if photo and allowed_file(photo.filename):
        filename = secure_filename(f"camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)
        
        try:
            # Predict disease
            predicted_class, confidence = disease_model.predict_disease(filepath)
            disease_name = DISEASE_CLASSES[predicted_class]
            
            # Get treatment recommendations
            treatment = get_treatment_recommendation(disease_name)
            
            # Save to database
            new_detection = DetectionHistory(
                user_id=current_user.id,
                image_path=filename,
                predicted_disease=disease_name,
                confidence=float(confidence),
                treatment_recommendation=treatment
            )
            db.session.add(new_detection)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'prediction': disease_name,
                'confidence': confidence,
                'treatment': treatment,
                'image_url': url_for('static', filename='uploads/' + filename)
            })
            
        except Exception as e:
            return jsonify({'error': f'Error processing image: {str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        message = request.form['message']
        language = request.form.get('language', 'en')
        
        # Generate AI response
        response = generate_chat_response(message, language)
        
        # Save to database
        new_chat = ChatMessage(
            user_id=current_user.id,
            message=message,
            response=response,
            language=language
        )
        db.session.add(new_chat)
        db.session.commit()
        
        return jsonify({'response': response})
    
    # Get chat history
    chat_history = ChatMessage.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatMessage.message_time.desc()).limit(10).all()
    
    return render_template('chat.html', chat_history=reversed(chat_history))

@app.route('/recommendations')
@login_required
def recommendations():
    disease = request.args.get('disease', '')
    
    if disease:
        recommendations_data = PestRecommendation.query.filter(
            PestRecommendation.disease_name.ilike(f'%{disease}%')
        ).all()
    else:
        recommendations_data = PestRecommendation.query.limit(10).all()
    
    return render_template('recommendations.html', recommendations=recommendations_data, search_disease=disease)

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_treatment_recommendation(disease_name):
    """Get treatment recommendations for a disease"""
    treatments = {
        'Early_blight': 'Use copper-based fungicides. Remove infected leaves. Practice crop rotation. Ensure proper plant spacing.',
        'Late_blight': 'Apply fungicides containing chlorothalonil. Remove and destroy infected plants. Avoid overhead watering.',
        'Powdery_mildew': 'Use sulfur-based fungicides. Improve air circulation. Apply neem oil every 7-10 days.',
        'Leaf_spot': 'Remove infected leaves. Apply copper fungicide. Avoid overhead watering.',
        'healthy': 'Plant is healthy! Continue good agricultural practices including proper watering and fertilization.'
    }
    
    for key, treatment in treatments.items():
        if key.lower() in disease_name.lower():
            return treatment
    
    return 'Consult local agricultural expert for specific treatment recommendations. Practice crop rotation and maintain plant health.'

def generate_chat_response(message, language='en'):
    """Generate AI response for chat"""
    message_lower = message.lower()
    
    responses = {
        'en': {
            'hello': 'Hello! I\'m your SmartAgriDoctor assistant. How can I help with plant disease diagnosis today?',
            'hi': 'Hi there! I can help you identify plant diseases and suggest treatments. What would you like to know?',
            'treatment': 'I can recommend treatments based on disease detection. Please upload a leaf image for accurate analysis.',
            'prevention': 'Good agricultural practices include crop rotation, proper spacing, regular monitoring, and balanced fertilization.',
            'blight': 'For blight diseases, remove infected leaves, apply copper-based fungicides, and avoid overhead watering.',
            'mildew': 'Powdery mildew can be treated with sulfur sprays, neem oil, or baking soda solutions. Improve air circulation.',
            'healthy': 'Maintain plant health with proper watering, balanced nutrition, and regular pest monitoring.',
            'default': 'I specialize in plant disease diagnosis. Please upload a leaf image for accurate analysis or ask about specific plant issues.'
        },
        'es': {
            'hola': '¡Hola! Soy tu asistente SmartAgriDoctor. ¿Cómo puedo ayudarte con el diagnóstico de enfermedades de plantas hoy?',
            'default': 'Me especializo en diagnóstico de enfermedades de plantas. Sube una imagen de hoja para análisis preciso.'
        },
        'fr': {
            'bonjour': 'Bonjour! Je suis votre assistant SmartAgriDoctor. Comment puis-je vous aider avec le diagnostic des maladies des plantes aujourd\'hui?',
            'default': 'Je me spécialise dans le diagnostic des maladies des plantes. Téléchargez une image de feuille pour une analyse précise.'
        }
    }
    
    lang_responses = responses.get(language, responses['en'])
    
    for key, response in lang_responses.items():
        if key in message_lower and key != 'default':
            return response
    
    return lang_responses.get('default', 'I can help with plant disease diagnosis. Please upload an image or ask specific questions.')

def init_db():
    """Initialize the database with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add sample pest recommendations
        sample_recommendations = [
            {
                'disease_name': 'Early Blight',
                'organic_treatment': 'Use neem oil spray. Apply compost tea. Remove infected leaves.',
                'chemical_treatment': 'Apply chlorothalonil or copper-based fungicides every 7-10 days.',
                'preventive_measures': 'Practice crop rotation. Ensure proper spacing. Water at soil level.',
                'suitable_crops': 'Tomato, Potato, Eggplant'
            },
            {
                'disease_name': 'Late Blight',
                'organic_treatment': 'Apply baking soda solution. Use compost tea. Remove infected plants.',
                'chemical_treatment': 'Use fungicides containing mancozeb or metalaxyl. Apply preventatively.',
                'preventive_measures': 'Avoid overhead watering. Provide good air circulation. Use resistant varieties.',
                'suitable_crops': 'Tomato, Potato'
            },
            {
                'disease_name': 'Powdery Mildew',
                'organic_treatment': 'Spray with milk solution (1:9 ratio). Use baking soda spray. Apply neem oil.',
                'chemical_treatment': 'Apply sulfur-based fungicides or potassium bicarbonate.',
                'preventive_measures': 'Maintain proper spacing. Ensure good air circulation. Avoid overhead watering.',
                'suitable_crops': 'Cucumber, Squash, Grapes, Roses'
            }
        ]
        
        for rec_data in sample_recommendations:
            if not PestRecommendation.query.filter_by(disease_name=rec_data['disease_name']).first():
                new_rec = PestRecommendation(**rec_data)
                db.session.add(new_rec)
        
        db.session.commit()
        print("✅ Database initialized successfully!")

if __name__ == '__main__':
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize database
    print("🔄 Initializing database...")
    init_db()
    
    print("🚀 Starting SmartAgriDoctor Server...")
    print("📍 Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)