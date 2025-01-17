import random
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
import warnings as wg
from prettytable import PrettyTable
import pyttsx3 as sp
import json
import os
from typing import Dict, List, Optional, Union

wg.simplefilter(action="ignore")

class Patient:
    def __init__(self, patient_id: int, age: int, first_name: str, last_name: str, gender: str, contact: str):
        self.patient_id = patient_id
        self.age = age
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.contact = contact
        self.room = None
        self.doctor_name = None
        self.appointment_time = None
        self.is_emergency = False
        self.admission_time = None
        self.queue_number = None
        self.estimated_wait_time = None
        self.medical_history = []
        self.prescriptions = []
        self.allergies = []
        self.blood_group = None
        self.insurance_details = {}
        self.emergency_contact = {}
        self.last_visit = None
        self.payment_status = "Pending"
        self.discharge_summary = None

    def add_medical_history(self, condition: str, date: datetime):
        self.medical_history.append({"condition": condition, "date": date})

    def add_prescription(self, medicine: str, dosage: str, duration: str):
        self.prescriptions.append({
            "medicine": medicine,
            "dosage": dosage,
            "duration": duration,
            "date_prescribed": datetime.now()
        })

    def update_insurance(self, provider: str, policy_number: str, coverage: float):
        self.insurance_details = {
            "provider": provider,
            "policy_number": policy_number,
            "coverage": coverage
        }

    def add_emergency_contact(self, name: str, relation: str, contact: str):
        self.emergency_contact = {
            "name": name,
            "relation": relation,
            "contact": contact
        }

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "name": f"{self.first_name} {self.last_name}",
            "age": self.age,
            "gender": self.gender,
            "contact": self.contact,
            "room": self.room,
            "doctor": self.doctor_name,
            "is_emergency": self.is_emergency,
            "queue_number": self.queue_number,
            "medical_history": self.medical_history,
            "prescriptions": self.prescriptions
        }

class EmergencyStack:
    def __init__(self):
        self.items = []
    
    def is_empty(self):
        return len(self.items) == 0
    
    def push(self, patient: Patient):
        self.items.append(patient)
    
    def pop(self) -> Optional[Patient]:
        if not self.is_empty():
            return self.items.pop()
        return None
    
    def peek(self) -> Optional[Patient]:
        if not self.is_empty():
            return self.items[-1]
        return None
    
    def size(self):
        return len(self.items)

class PatientNode:
    def __init__(self, patient: Patient):
        self.patient = patient
        self.left = None
        self.right = None

class PatientBST:
    def __init__(self):
        self.root = None
    
    def insert(self, patient: Patient):
        if not self.root:
            self.root = PatientNode(patient)
        else:
            self._insert_recursive(self.root, patient)
    
    def _insert_recursive(self, node: PatientNode, patient: Patient):
        if patient.patient_id < node.patient.patient_id:
            if node.left is None:
                node.left = PatientNode(patient)
            else:
                self._insert_recursive(node.left, patient)
        else:
            if node.right is None:
                node.right = PatientNode(patient)
            else:
                self._insert_recursive(node.right, patient)
    
    def search(self, patient_id: int) -> Optional[Patient]:
        return self._search_recursive(self.root, patient_id)
    
    def _search_recursive(self, node: PatientNode, patient_id: int) -> Optional[Patient]:
        if node is None or node.patient.patient_id == patient_id:
            return node.patient if node else None
        
        if patient_id < node.patient.patient_id:
            return self._search_recursive(node.left, patient_id)
        return self._search_recursive(node.right, patient_id)
    
    def inorder_traversal(self) -> List[Patient]:
        patients = []
        self._inorder_recursive(self.root, patients)
        return patients
    
    def _inorder_recursive(self, node: PatientNode, patients: List[Patient]):
        if node:
            self._inorder_recursive(node.left, patients)
            patients.append(node.patient)
            self._inorder_recursive(node.right, patients)

class QueueManager:
    def __init__(self):
        self.regular_queue = deque()
        self.emergency_queue = deque()
        self.current_queue_number = 1000
        self.average_service_time = 15  # minutes
        self.max_waiting_time = 120  # minutes
        self.queue_history = []
        self.service_counters = 3
        self.active_counters = set()
        self.priority_levels = {
            "Critical": 1,
            "High": 2,
            "Medium": 3,
            "Low": 4
        }

    def generate_queue_number(self) -> int:
        self.current_queue_number += 1
        return self.current_queue_number

    def calculate_wait_time(self, queue_position: int, is_emergency: bool) -> int:
        base_time = queue_position * (self.average_service_time / self.service_counters)
        if is_emergency:
            return min(base_time / 2, self.max_waiting_time)
        return min(base_time, self.max_waiting_time)

    def add_to_queue(self, patient: Patient, is_emergency: bool = False, priority: str = "Medium") -> str:
        patient.queue_number = self.generate_queue_number()
        queue_position = len(self.emergency_queue if is_emergency else self.regular_queue)
        patient.estimated_wait_time = self.calculate_wait_time(queue_position, is_emergency)

        queue_entry = {
            "patient": patient,
            "entry_time": datetime.now(),
            "priority": priority,
            "priority_level": self.priority_levels.get(priority, 3)
        }

        if is_emergency:
            self.emergency_queue.append(queue_entry)
            queue_id = f"E{patient.queue_number}"
        else:
            self.regular_queue.append(queue_entry)
            queue_id = f"R{patient.queue_number}"

        self.queue_history.append({
            "queue_id": queue_id,
            "patient_id": patient.patient_id,
            "entry_time": datetime.now(),
            "is_emergency": is_emergency,
            "priority": priority,
            "estimated_wait": patient.estimated_wait_time
        })

        return queue_id

    def get_next_patient(self) -> Optional[Patient]:
        if not self.emergency_queue and not self.regular_queue:
            return None

        if self.emergency_queue:
            sorted_emergency = sorted(
                self.emergency_queue,
                key=lambda x: (x["priority_level"], x["entry_time"])
            )
            entry = sorted_emergency[0]
            self.emergency_queue.remove(entry)
            return entry["patient"]

        if self.regular_queue:
            sorted_regular = sorted(
                self.regular_queue,
                key=lambda x: (x["priority_level"], x["entry_time"])
            )
            entry = sorted_regular[0]
            self.regular_queue.remove(entry)
            return entry["patient"]

        return None

    def update_wait_times(self):
        for i, entry in enumerate(sorted(self.emergency_queue, key=lambda x: x["priority_level"])):
            patient = entry["patient"]
            patient.estimated_wait_time = self.calculate_wait_time(i, True)

        emergency_count = len(self.emergency_queue)
        for i, entry in enumerate(sorted(self.regular_queue, key=lambda x: x["priority_level"])):
            patient = entry["patient"]
            patient.estimated_wait_time = self.calculate_wait_time(emergency_count + i, False)

    def get_queue_statistics(self) -> dict:
        return {
            "total_patients": len(self.emergency_queue) + len(self.regular_queue),
            "emergency_patients": len(self.emergency_queue),
            "regular_patients": len(self.regular_queue),
            "average_wait_time": self.calculate_average_wait_time(),
            "max_wait_time": self.get_max_wait_time(),
            "active_counters": len(self.active_counters)
        }

    def calculate_average_wait_time(self) -> float:
        all_wait_times = [entry["patient"].estimated_wait_time for entry in self.emergency_queue]
        all_wait_times.extend([entry["patient"].estimated_wait_time for entry in self.regular_queue])
        return sum(all_wait_times) / len(all_wait_times) if all_wait_times else 0

    def get_max_wait_time(self) -> int:
        all_wait_times = [entry["patient"].estimated_wait_time for entry in self.emergency_queue]
        all_wait_times.extend([entry["patient"].estimated_wait_time for entry in self.regular_queue])
        return max(all_wait_times) if all_wait_times else 0

class HospitalManagementSystem:
    def __init__(self):
        self.queue_manager = QueueManager()
        self.admitted_patients: Dict[int, Patient] = {}
        self.room_numbers = list(range(101, 201))
        self.occupied_rooms = set()
        self.doctors = self.initialize_doctors()
        self.patient_history = []
        self.discharge_history = []
        self.appointments = []
        self.voice_engine = sp.init()
        self.department_stats = {}
        self.billing_records = []
        self.inventory = {}
        self.staff_schedule = {}
        self.maintenance_log = []
        self.emergency_stack = EmergencyStack()
        self.patient_bst = PatientBST()

    def initialize_doctors(self) -> Dict[str, str]:
        return {
            "Dr. Alice Smith": "Cardiologist",
            "Dr. Bob Johnson": "Neurologist",
            "Dr. Catherine Lee": "Pediatrician",
            "Dr. David Brown": "Orthopedist",
            "Dr. Emily Davis": "General Physician",
            "Dr. Frank Wilson": "Surgeon",
            "Dr. Grace Martinez": "Dermatologist",
            "Dr. Henry Clark": "Psychiatrist",
            "Dr. Isabelle White": "Gynecologist",
            "Dr. John Lewis": "ENT Specialist"
        }

    def add_patient(self, is_emergency: bool = False):
        try:
            patient_id = int(input("Enter patient ID: "))
            age = int(input("Enter age: "))
            first_name = input("Enter first name: ").strip()
            last_name = input("Enter last name: ").strip()
            gender = input("Enter gender (M/F/O): ").strip().upper()
            contact = input("Enter contact number: ").strip()

            patient = Patient(patient_id, age, first_name, last_name, gender, contact)
            patient.is_emergency = is_emergency
            patient.admission_time = datetime.now()

            blood_group = input("Enter blood group (A+/A-/B+/B-/O+/O-/AB+/AB-): ").strip().upper()
            if blood_group not in ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]:
                raise ValueError("Invalid blood group")
            patient.blood_group = blood_group

            ec_name = input("Enter emergency contact name: ").strip()
            ec_relation = input("Enter relationship to patient: ").strip()
            ec_contact = input("Enter emergency contact number: ").strip()
            patient.add_emergency_contact(ec_name, ec_relation, ec_contact)

            has_insurance = input("Does patient have insurance? (y/n): ").lower() == 'y'
            if has_insurance:
                provider = input("Enter insurance provider: ").strip()
                policy_number = input("Enter policy number: ").strip()
                coverage = float(input("Enter coverage amount: "))
                patient.update_insurance(provider, policy_number, coverage)

            while True:
                condition = input("Enter medical condition (or 'done' to finish): ").strip()
                if condition.lower() == 'done':
                    break
                date_str = input("Enter date of condition (YYYY-MM-DD): ").strip()
                condition_date = datetime.strptime(date_str, "%Y-%m-%d")
                patient.add_medical_history(condition, condition_date)

            # Add patient to BST
            self.patient_bst.insert(patient)
            
            # Add emergency patients to stack
            if is_emergency:
                self.emergency_stack.push(patient)

            priority = "Critical" if is_emergency else input("Enter priority (High/Medium/Low): ").strip()
            queue_number = self.queue_manager.add_to_queue(patient, is_emergency, priority)

            self.show_doctors_list()
            doctor_name = input("Enter doctor name from the list: ").strip()
            while doctor_name not in self.doctors:
                print("Invalid doctor name. Please choose from the list.")
                doctor_name = input("Enter doctor name from the list: ")
            
            patient.doctor_name = doctor_name
            appointment_time = datetime.now() + timedelta(minutes=patient.estimated_wait_time)
            self.schedule_appointment(patient, doctor_name, appointment_time)

            self.add_to_history(patient)

            announcement = f"Queue number {queue_number} for {patient.first_name} {patient.last_name}"
            print(f"\n{announcement}")
            self.speak(announcement)

            if is_emergency:
                print(f"EMERGENCY CASE - Estimated wait time: {patient.estimated_wait_time} minutes")
            else:
                print(f"Regular case - Estimated wait time: {patient.estimated_wait_time} minutes")

        except ValueError as e:
            print(f"Invalid input: {str(e)}")

    def search_patient_record(self, patient_id: int) -> Optional[Patient]:
        return self.patient_bst.search(patient_id)

    def process_patient(self):
        patient = self.queue_manager.get_next_patient()

        if not patient:
            if self.emergency_stack.is_empty():
                print("No patients in queue or emergency stack.")
                return
            patient = self.emergency_stack.pop()

        print(f"Processing {'emergency' if patient.is_emergency else 'regular'} patient: {patient.first_name} {patient.last_name}")

        # Assign room
        available_rooms = set(self.room_numbers) - self.occupied_rooms
        if not available_rooms:
            print("No rooms available!")
            # Put the patient back in appropriate queue
            if patient.is_emergency:
                self.emergency_stack.push(patient)
            else:
                self.queue_manager.add_to_queue(patient, patient.is_emergency)
            return

        room = min(available_rooms)
        patient.room = room
        self.occupied_rooms.add(room)
        self.admitted_patients[patient.patient_id] = patient

        # Update patient status in history
        for record in self.patient_history:
            if record["Patient ID"] == patient.patient_id:
                record["Status"] = "Admitted"
                record["Room"] = room
                break

        print(f"Patient admitted to room {room}")

        # Update queue statistics
        self.queue_manager.update_wait_times()

    def show_doctors_list(self):
        print("\nAvailable Doctors:")
        for doctor, specialty in self.doctors.items():
            print(f"{doctor} - {specialty}")

    def add_to_history(self, patient: Patient):
        history_record = {
            "Patient ID": patient.patient_id,
            "Name": f"{patient.first_name} {patient.last_name}",
            "Age": patient.age,
            "Gender": patient.gender,
            "Blood Group": patient.blood_group,
            "Doctor": patient.doctor_name,
            "Type": "Emergency" if patient.is_emergency else "Regular",
            "Queue Number": patient.queue_number,
            "Timestamp": datetime.now(),
            "Status": "Waiting",
            "Estimated Wait Time": f"{patient.estimated_wait_time} minutes",
            "Medical History": patient.medical_history,
            "Insurance": patient.insurance_details,
            "Emergency Contact": patient.emergency_contact
        }
        self.patient_history.append(history_record)

    def schedule_appointment(self, patient: Patient, doctor_name: str, appointment_time: datetime):
        appointment = {
            "patient": patient,
            "doctor_name": doctor_name,
            "time": appointment_time,
            "status": "Scheduled",
            "department": self.doctors[doctor_name],
            "notes": "",
            "follow_up": None
        }
        self.appointments.append(appointment)
        print(f"Appointment scheduled with {doctor_name} at {appointment_time.strftime('%Y-%m-%d %H:%M')}")

    def speak(self, text: str):
        try:
            self.voice_engine.say(text)
            self.voice_engine.runAndWait()
        except:
            pass

    def show_patient_history(self):
        if not self.patient_history:
            print("No patient history available.")
            return

        print("\nPatient History:")
        table = PrettyTable()
        table.field_names = ["ID", "Name", "Type", "Status", "Doctor", "Queue Number", "Wait Time"]
        for record in self.patient_history:
            table.add_row([
                record["Patient ID"],
                record["Name"],
                record["Type"],
                record["Status"],
                record["Doctor"],
                record["Queue Number"],
                record["Estimated Wait Time"]
            ])
        print(table)

    def show_current_patients(self):
        if not self.admitted_patients:
            print("No current patients.")
            return

        print("\nCurrent Admitted Patients:")
        table = PrettyTable()
        table.field_names = ["ID", "Name", "Room", "Doctor", "Admission Time"]
        for patient in self.admitted_patients.values():
            table.add_row([
                patient.patient_id,
                f"{patient.first_name} {patient.last_name}",
                patient.room,
                patient.doctor_name,
                patient.admission_time.strftime("%Y-%m-%d %H:%M")
            ])
        print(table)

    def show_department_stats(self):
        department_counts = {}
        for doctor, specialty in self.doctors.items():
            department_counts[specialty] = sum(1 for p in self.admitted_patients.values() if p.doctor_name == doctor)

        print("\nDepartment Statistics:")
        table = PrettyTable()
        table.field_names = ["Department", "Current Patients"]
        for dept, count in department_counts.items():
            table.add_row([dept, count])
        print(table)

    def show_billing_summary(self):
        if not self.billing_records:
            print("No billing records available.")
            return

        print("\nBilling Summary:")
        table = PrettyTable()
        table.field_names = ["Patient ID", "Name", "Total Amount", "Insurance Coverage", "Final Amount"]
        for bill in self.billing_records:
            table.add_row([
                bill["patient_id"],
                bill["patient_name"],
                f"${bill['total']:.2f}",
                f"${bill['insurance_coverage']:.2f}",
                f"${bill['final_amount']:.2f}"
            ])
        print(table)

    def show_inventory_status(self):
        if not self.inventory:
            print("No inventory records available.")
            return

        print("\nInventory Status:")
        for category, items in self.inventory.items():
            print(f"\n{category.capitalize()}:")
            table = PrettyTable()
            table.field_names = ["Item", "Quantity", "Unit Price", "Last Updated"]
            for item, details in items.items():
                table.add_row([
                    item,
                    details["quantity"],
                    f"${details['unit_price']:.2f}",
                    details["last_updated"].strftime("%Y-%m-%d")
                ])
            print(table)
    def update_stock(self, category: str, item: str, quantity: int,):
        """
        Updates the stock of an existing item in the inventory.

        Parameters:
            category (str): The category of the item (e.g., 'medications', 'supplies').
            item (str): The name of the item to update.
            quantity (int): The quantity to add (positive) or remove (negative).

        Raises:
            ValueError: If the item does not exist in the category or if the resulting quantity is negative.
        """
        from datetime import datetime

        if category not in self.inventory or item not in self.inventory[category]:
            raise ValueError(f"Item '{item}' does not exist in category '{category}'.")

        current_quantity = self.inventory[category][item]['quantity']
        new_quantity = current_quantity + quantity

        if new_quantity < 0:
            raise ValueError(f"Cannot reduce stock of '{item}' below 0. Current quantity: {current_quantity}.")

        # Update the quantity and last updated date
        self.inventory[category][item]['quantity'] = new_quantity
        self.inventory[category][item]['last_updated'] = datetime.now()

        print(f"Stock of '{item}' in category '{category}' updated. New quantity: {new_quantity}.")


    def room_management_menu(self):
        while True:
            print("\n----- Room Management Menu -----")
            print("1. View Available Rooms")
            print("2. View Occupied Rooms")
            print("3. Assign Room")
            print("4. Release Room")
            print("5. Back to Main Menu")
            
            choice = input("\nEnter your choice (1-5): ")
            
            if choice == '1':
                available = set(self.room_numbers) - self.occupied_rooms
                print(f"\nAvailable Rooms: {sorted(list(available))}")
            elif choice == '2':
                print(f"\nOccupied Rooms: {sorted(list(self.occupied_rooms))}")
            elif choice == '3':
                # Room assignment is handled in process_patient
                print("Room assignment is handled automatically during patient processing.")
            elif choice == '4':
                room = int(input("Enter room number to release: "))
                if room in self.occupied_rooms:
                    self.occupied_rooms.remove(room)
                    print(f"Room {room} has been released.")
                else:
                    print("Room is not occupied.")
            elif choice == '5':
                break
            else:
                print("Invalid choice. Please try again.")

    def appointment_management_menu(self):
        while True:
            print("\n----- Appointment Management Menu -----")
            print("1. View All Appointments")
            print("2. Schedule New Appointment")
            print("3. Cancel Appointment")
            print("4. Back to Main Menu")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '1':
                self.show_appointments()
            elif choice == '2':
                # Appointment scheduling is handled in add_patient
                print("Appointments are scheduled during patient registration.")
            elif choice == '3':
                # Add appointment cancellation functionality
                print("Appointment cancellation functionality to be implemented.")
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please try again.")

    def show_appointments(self):
        if not self.appointments:
            print("No appointments scheduled.")
            return

        print("\nScheduled Appointments:")
        table = PrettyTable()
        table.field_names = ["Patient", "Doctor", "Time", "Status", "Department"]
        for apt in self.appointments:
            patient = apt["patient"]
            table.add_row([
                f"{patient.first_name} {patient.last_name}",
                apt["doctor_name"],
                apt["time"].strftime("%Y-%m-%d %H:%M"),
                apt["status"],
                apt["department"]
            ])
        print(table)

    def billing_menu(self):
        while True:
            print("\n----- Billing Menu -----")
            print("1. Generate Bill")
            print("2. View Billing History")
            print("3. Update Payment Status")
            print("4. Back to Main Menu")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '1':
                patient_id = int(input("Enter patient ID: "))
                patient = self.search_patient_record(patient_id)
                if patient:
                    bill = self.generate_bill(patient)
                    print("\nBill generated successfully:")
                    print(f"Total Amount: ${bill['total']:.2f}")
                    print(f"Insurance Coverage: ${bill['insurance_coverage']:.2f}")
                    print(f"Final Amount: ${bill['final_amount']:.2f}")
                else:
                    print("Patient not found.")
            elif choice == '2':
                self.show_billing_summary()
            elif choice == '3':
                # Add payment status update functionality
                print("Payment status update functionality to be implemented.")
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please try again.")

    def inventory_menu(self):
        while True:
            print("\n----- Inventory Menu -----")
            print("1. View Inventory")
            print("2. Add Item")
            print("3. Update Stock")
            print("4. Back to Main Menu")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '1':
                self.show_inventory_status()
            elif choice == '2':
                category = input("Enter category (medications/equipment/supplies): ").lower()
                item = input("Enter item name: ")
                quantity = int(input("Enter quantity: "))
                price = float(input("Enter unit price: "))
                self.add_to_inventory(category, item, quantity, price)
            elif choice == '3':
                self.update_stock(category, item, quantity, )
            elif choice == '4':
                break
            else:
                print("Invalid choice. Please try again.")
     
     
    def add_to_inventory(self, category: str, item: str, quantity: int, unit_price: float):
        """
        Adds or updates an item in the inventory.

        Parameters:
            category (str): The category of the item (e.g., 'medications', 'supplies').
            item (str): The name of the item to add or update.
            quantity (int): The quantity to add.
            unit_price (float): The unit price of the item.
        """
        from datetime import datetime

        if category not in self.inventory:
            self.inventory[category] = {}

        if item in self.inventory[category]:
            # Update existing item
            self.inventory[category][item]['quantity'] += quantity
            self.inventory[category][item]['unit_price'] = unit_price
            self.inventory[category][item]['last_updated'] = datetime.now()
        else:
            # Add new item
            self.inventory[category][item] = {
                'quantity': quantity,
                'unit_price': unit_price,
                'last_updated': datetime.now()
            }

        print(f"Item '{item}' added/updated in category '{category}'.")
    
    def generate_bill(self, patient: Patient) -> dict:
        """
        Generates a bill for a patient.

        Parameters:
            patient (Patient): The patient for whom the bill is being generated.

        Returns:
            dict: A summary of the bill containing total, insurance coverage, and final amount.
        """
        # Example charges (these could be more dynamic in a complete system)
        room_charge = 500 if patient.room else 0
        doctor_fee = 200
        medication_cost = sum([100 for _ in patient.prescriptions])  # Assume $100 per prescription

        # Calculate total
        total = room_charge + doctor_fee + medication_cost

        # Insurance coverage
        insurance_coverage = patient.insurance_details.get("coverage", 0)
        final_amount = total - insurance_coverage

        # Store billing record
        bill_summary = {
            "patient_id": patient.patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "total": total,
            "insurance_coverage": insurance_coverage,
            "final_amount": max(final_amount, 0)  # Avoid negative amounts
        }
        self.billing_records.append(bill_summary)

        print(f"Bill generated for {patient.first_name} {patient.last_name}. Total: ${total}, Final: ${final_amount}")
        return bill_summary
       
    def patient_management_menu(self):
        while True:
            print("\n" + "=" * 50)
            print("           Patient Management Menu")
            print("=" * 50)
            print("1. Add New Patient")
            print("2. Add Emergency Patient")
            print("3. View Patient Details")
            print("4. Update Patient Information")
            print("5. Search Patient Record")
            print("6. View All Patients")
            print("7. Process Next Patient")
            print("8. Process Emergency Patient")
            print("9. Back to Main Menu")
            print("=" * 50)

            choice = input("\nEnter your choice (1-9): ")

            try:
                if choice == '1':
                    self.add_patient(is_emergency=False)

                elif choice == '2':
                    self.add_patient(is_emergency=True)

                elif choice == '3':
                    patient_id = int(input("Enter patient ID: "))
                    patient = self.search_patient_record(patient_id)
                    if patient:
                        self.display_patient_details(patient)
                    else:
                        print("Patient not found.")

                elif choice == '4':
                    patient_id = int(input("Enter patient ID: "))
                    patient = self.search_patient_record(patient_id)
                    if patient:
                        self.update_patient_information(patient)
                    else:
                        print("Patient not found.")

                elif choice == '5':
                    patient_id = int(input("Enter patient ID to search: "))
                    patient = self.search_patient_record(patient_id)
                    if patient:
                        self.display_patient_details(patient)
                    else:
                        print("Patient not found.")

                elif choice == '6':
                    self.view_all_patients()

                elif choice == '7':
                    self.process_patient()

                

                elif choice == '9':
                    break
                
                else:
                    print("Invalid choice. Please try again.")

            except ValueError as e:
                print(f"Error: {str(e)}")
            
    def display_patient_details(self, patient: Patient):
        print("\n" + "=" * 50)
        print("           Patient Details")
        print("=" * 50)
        print(f"Patient ID: {patient.patient_id}")
        print(f"Name: {patient.first_name} {patient.last_name}")
        print(f"Age: {patient.age}")
        print(f"Gender: {patient.gender}")
        print(f"Blood Group: {patient.blood_group}")
        print(f"Contact: {patient.contact}")
        print(f"Room: {patient.room if patient.room else 'Not assigned'}")
        print(f"Doctor: {patient.doctor_name if patient.doctor_name else 'Not assigned'}")
        print(f"Emergency Status: {'Yes' if patient.is_emergency else 'No'}")
        
        print("\nMedical History:")
        if patient.medical_history:
            for history in patient.medical_history:
                print(f"- {history['condition']} (Date: {history['date'].strftime('%Y-%m-%d')})")
        else:
            print("No medical history recorded")
        
        print("\nPrescriptions:")
        if patient.prescriptions:
            for prescription in patient.prescriptions:
                print(f"- Medicine: {prescription['medicine']}")
                print(f"  Dosage: {prescription['dosage']}")
                print(f"  Duration: {prescription['duration']}")
                print(f"  Prescribed: {prescription['date_prescribed'].strftime('%Y-%m-%d')}")
        else:
            print("No prescriptions recorded")
        
        print("\nEmergency Contact:")
        if patient.emergency_contact:
            print(f"Name: {patient.emergency_contact['name']}")
            print(f"Relation: {patient.emergency_contact['relation']}")
            print(f"Contact: {patient.emergency_contact['contact']}")
            
        print("\nInsurance Details:")
        if patient.insurance_details:
            print(f"Provider: {patient.insurance_details['provider']}")
            print(f"Policy Number: {patient.insurance_details['policy_number']}")
            print(f"Coverage: ${patient.insurance_details['coverage']:.2f}")
        else:
            print("No insurance information recorded")
            
    def update_patient_information(self, patient: Patient):
        print("\n" + "=" * 50)
        print("           Update Patient Information")
        print("=" * 50)
        print("1. Update Contact Information")
        print("2. Add Medical History")
        print("3. Add Prescription")
        print("4. Update Insurance Details")
        print("5. Update Emergency Contact")
        print("6. Back")
        
        choice = input("\nEnter your choice (1-6): ")
        
        try:
            if choice == '1':
                patient.contact = input("Enter new contact number: ").strip()
                print("Contact information updated successfully.")
                
            elif choice == '2':
                condition = input("Enter medical condition: ").strip()
                date_str = input("Enter date (YYYY-MM-DD): ").strip()
                condition_date = datetime.strptime(date_str, "%Y-%m-%d")
                patient.add_medical_history(condition, condition_date)
                print("Medical history added successfully.")
                
            elif choice == '3':
                medicine = input("Enter medicine name: ").strip()
                dosage = input("Enter dosage: ").strip()
                duration = input("Enter duration: ").strip()
                patient.add_prescription(medicine, dosage, duration)
                print("Prescription added successfully.")
                
            elif choice == '4':
                provider = input("Enter insurance provider: ").strip()
                policy_number = input("Enter policy number: ").strip()
                coverage = float(input("Enter coverage amount: "))
                patient.update_insurance(provider, policy_number, coverage)
                print("Insurance details updated successfully.")
                
            elif choice == '5':
                name = input("Enter emergency contact name: ").strip()
                relation = input("Enter relationship to patient: ").strip()
                contact = input("Enter emergency contact number: ").strip()
                patient.add_emergency_contact(name, relation, contact)
                print("Emergency contact updated successfully.")
                
            elif choice == '6':
                return
                
            else:
                print("Invalid choice. Please try again.")
                
        except ValueError as e:
            print(f"Error: {str(e)}")
            
    def view_all_patients(self):
        if not self.patient_bst.root:
            print("No patients registered in the system.")
            return
            
        patients = self.patient_bst.inorder_traversal()
        
        print("\n" + "=" * 50)
        print("           All Patients")
        print("=" * 50)
        
        table = PrettyTable()
        table.field_names = ["ID", "Name", "Age", "Gender", "Room", "Doctor", "Status"]
        
        for patient in patients:
            status = "Emergency" if patient.is_emergency else "Regular"
            if patient.room:
                status = "Admitted"
                
            table.add_row([
                patient.patient_id,
                f"{patient.first_name} {patient.last_name}",
                patient.age,
                patient.gender,
                patient.room if patient.room else "Not assigned",
                patient.doctor_name if patient.doctor_name else "Not assigned",
                status
            ])
            
        print(table)

    def show_reports_menu(self):
        while True:
            print("\n----- Reports Menu -----")
            print("1. Patient History Report")
            print("2. Department Statistics")
            print("3. Occupancy Report")
            print("4. Appointment Summary")
            print("5. Queue Analysis Report")
            print("6. Financial Summary")
            print("7. Back to Main Menu")

            choice = input("\nEnter your choice (1-7): ")

            if choice == '1':
                self.show_patient_history()

            elif choice == '2':
                self.show_department_stats()
                # Additional department analytics
                if self.patient_history:
                    df = pd.DataFrame(self.patient_history)
                    print("\nDepartment Workload Analysis:")
                    dept_counts = df.groupby("Doctor")["Patient ID"].count()
                    print(dept_counts)

            elif choice == '3':
                print("\nOccupancy Report:")
                total_rooms = len(self.room_numbers)
                occupied = len(self.occupied_rooms)
                occupancy_rate = (occupied / total_rooms) * 100

                table = PrettyTable()
                table.field_names = ["Total Rooms", "Occupied", "Available", "Occupancy Rate"]
                table.add_row([
                    total_rooms,
                    occupied,
                    total_rooms - occupied,
                    f"{occupancy_rate:.1f}%"
                ])
                print(table)

            elif choice == '4':
                if self.appointments:
                    print("\nAppointment Summary Report:")
                    dept_appointments = {}
                    for apt in self.appointments:
                        dept = apt["department"]
                        dept_appointments[dept] = dept_appointments.get(dept, 0) + 1

                    table = PrettyTable()
                    table.field_names = ["Department", "Total Appointments"]
                    for dept, count in dept_appointments.items():
                        table.add_row([dept, count])
                    print(table)

                    # Today's appointments
                    today = datetime.now().date()
                    today_appointments = [apt for apt in self.appointments 
                                       if apt["time"].date() == today]
                    print(f"\nToday's Appointments: {len(today_appointments)}")
                else:
                    print("No appointments to report.")

            elif choice == '5':
                stats = self.queue_manager.get_queue_statistics()
                print("\nQueue Analysis Report:")
                table = PrettyTable()
                table.field_names = ["Metric", "Value"]
                table.add_row(["Total Patients in Queue", stats['total_patients']])
                table.add_row(["Emergency Patients", stats['emergency_patients']])
                table.add_row(["Regular Patients", stats['regular_patients']])
                table.add_row(["Average Wait Time", f"{stats['average_wait_time']:.1f} minutes"])
                table.add_row(["Maximum Wait Time", f"{stats['max_wait_time']} minutes"])
                print(table)

                # Queue history analysis
                if self.queue_manager.queue_history:
                    df = pd.DataFrame(self.queue_manager.queue_history)
                    print("\nQueue History Analysis:")
                    print(f"Total Patients Processed: {len(df)}")
                    print(f"Emergency Cases: {len(df[df['is_emergency']])}")
                    avg_wait = df['estimated_wait'].mean()
                    print(f"Average Wait Time: {avg_wait:.1f} minutes")

            elif choice == '6':
                print("\nFinancial Summary Report:")
                if self.billing_records:
                    total_revenue = sum(bill['total'] for bill in self.billing_records)
                    total_insurance = sum(bill['insurance_coverage'] for bill in self.billing_records)
                    total_final = sum(bill['final_amount'] for bill in self.billing_records)

                    table = PrettyTable()
                    table.field_names = ["Metric", "Amount"]
                    table.add_row(["Total Revenue", f"${total_revenue:.2f}"])
                    table.add_row(["Insurance Coverage", f"${total_insurance:.2f}"])
                    table.add_row(["Net Revenue", f"${total_final:.2f}"])
                    table.add_row(["Average Bill Amount", f"${(total_revenue/len(self.billing_records)):.2f}"])
                    print(table)
                else:
                    print("No billing records available.")

            elif choice == '7':
                break

            else:
                print("Invalid choice. Please try again.")
    def show_queue_status(self):
        print("\n" + "=" * 50)
        print("           Queue Status")
        print("=" * 50)

        stats = self.queue_manager.get_queue_statistics()

        print("\nQueue Statistics:")
        print(f"Total Patients in Queue: {stats['total_patients']}")
        print(f"Emergency Patients: {stats['emergency_patients']}")
        print(f"Regular Patients: {stats['regular_patients']}")
        print(f"Average Wait Time: {stats['average_wait_time']:.1f} minutes")
        print(f"Maximum Wait Time: {stats['max_wait_time']} minutes")

        # Emergency Stack Status
        print("\nEmergency Stack Status:")
        if self.emergency_stack.is_empty():
            print("No patients in emergency stack")
        else:
            table = PrettyTable()
            table.field_names = ["Position", "Patient ID", "Name", "Priority"]

            for i, patient in enumerate(reversed(self.emergency_stack.items), 1):
                table.add_row([
                    i,
                    patient.patient_id,
                    f"{patient.first_name} {patient.last_name}",
                    "Critical"
                ])
            print(table)

        # Emergency Queue Status
        print("\nEmergency Queue Status:")
        if not self.queue_manager.emergency_queue:
            print("No patients in emergency queue")
        else:
            table = PrettyTable()
            table.field_names = ["Queue Number", "Patient ID", "Name", "Priority", "Wait Time"]

            sorted_emergency = sorted(
                self.queue_manager.emergency_queue,
                key=lambda x: (x["priority_level"], x["entry_time"])
            )

            for entry in sorted_emergency:
                patient = entry["patient"]
                table.add_row([
                    f"E{patient.queue_number}",
                    patient.patient_id,
                    f"{patient.first_name} {patient.last_name}",
                    entry["priority"],
                    f"{patient.estimated_wait_time} min"
                ])
            print(table)

        # Regular Queue Status
        print("\nRegular Queue Status:")
        if not self.queue_manager.regular_queue:
            print("No patients in regular queue")
        else:
            table = PrettyTable()
            table.field_names = ["Queue Number", "Patient ID", "Name", "Priority", "Wait Time"]

            sorted_regular = sorted(
                self.queue_manager.regular_queue,
                key=lambda x: (x["priority_level"], x["entry_time"])
            )

            for entry in sorted_regular:
                patient = entry["patient"]
                table.add_row([
                    f"R{patient.queue_number}",
                    patient.patient_id,
                    f"{patient.first_name} {patient.last_name}",
                    entry["priority"],
                    f"{patient.estimated_wait_time} min"
                ])
            print(table)

    def main_menu(self):
        while True:
            print("\n" + "=" * 50)
            print("           H-A-F-M Hospital Management System")
            print("=" * 50)
            print("1. Patient Management")
            print("2. Queue Management")
            print("3. Room Management")
            print("4. Appointment Management")
            print("5. Reports")
            print("6. Billing")
            print("7. Inventory")
            print("8. Exit")
            print("=" * 50)
            
            choice = input("\nEnter your choice (1-8): ")
            
            if choice == '1':
                self.patient_management_menu()
            elif choice == '2':
                self.show_queue_status()
            elif choice == '3':
                self.room_management_menu()
            elif choice == '4':
                self.appointment_management_menu()
            elif choice == '5':
                self.show_reports_menu()
            elif choice == '6':
                self.billing_menu()
            elif choice == '7':
                self.inventory_menu()
            elif choice == '8':
                self.speak("Thank you for using H-A-F-M Hospital Management System")
                print("Thank you for using H-A-F-M Hospital Management System")
                break
            else:
                print("Invalid choice. Please try again.")

def main():
    hospital = HospitalManagementSystem()
    hospital.main_menu()

if __name__ == "__main__":
    main()
            
        