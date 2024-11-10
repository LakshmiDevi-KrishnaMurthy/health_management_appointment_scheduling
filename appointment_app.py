from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import requests

app = Flask(__name__)
mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb.default.svc.cluster.local:27017")
client = MongoClient(mongo_uri)
db = client.health_records
appointments_collection = db.appointments

BILLING_SERVICE_URL = os.getenv("BILLING_SERVICE_URL", "http://localhost:30002")

def check_if_patient_has_bills(patient_id):
    """Check if the patient has any bills"""
    response = requests.get(f"{BILLING_SERVICE_URL}/bills/{patient_id}")
    if response.status_code == 200:
        bills = response.json()
        return len(bills) > 0
    return False

@app.route('/appointments', methods=['POST'])
def schedule_appointment():
    data = request.json
    patient_id = data.get('patient_id')

    if check_if_patient_has_bills(patient_id):
        return jsonify({"error": "Patient has outstanding bills, cannot schedule appointment"}), 400

    appointment_id = appointments_collection.insert_one(data).inserted_id
    return jsonify({"status": "Appointment scheduled", "appointment_id": str(appointment_id)}), 201

@app.route('/appointments/<appointment_id>', methods=['GET'])
def get_appointment(appointment_id):
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})
    if appointment:
        appointment['_id'] = str(appointment['_id'])  # Convert ObjectId to string
        return jsonify(appointment), 200
    else:
        return jsonify({"error": "Appointment not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
