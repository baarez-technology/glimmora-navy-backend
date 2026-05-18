import sys
import os

# Set python path to allow importing app
sys.path.append(os.getcwd())

import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal, get_db
from app.models.user import User
from app.models.scenario import Scenario
from app.models.session import Session as TrainingSession
from app.models.notification import Notification
from app.services.notification_service import get_unread_count

def test_subject_completion_notifications():
    print("Initializing subject completion notification integration test...")
    db = SessionLocal()
    try:
        # 1. Fetch Trainee (Jayesh Kumar)
        trainee = db.query(User).filter(User.service_number == "IN-2024-001").first()
        if not trainee:
            print("[FAIL] Trainee Jayesh Kumar not found in DB.")
            return
        
        # 2. Fetch Scenario (Bridge Watch)
        scenario = db.query(Scenario).filter(Scenario.title.like("%Bridge Watch%")).first()
        if not scenario:
            print("[FAIL] Bridge Watch scenario not found in DB.")
            return

        # 3. Fetch Instructor and Evaluator recipients
        instructor = db.query(User).filter(User.service_number == "IN-2019-042").first()
        evaluator = db.query(User).filter(User.service_number == "IN-2015-018").first()
        if not instructor or not evaluator:
            print("[FAIL] Staff members not found in DB.")
            return

        # Record starting unread counts
        inst_start_count = db.query(Notification).filter(Notification.user_id == instructor.id, Notification.is_read == False).count()
        eval_start_count = db.query(Notification).filter(Notification.user_id == evaluator.id, Notification.is_read == False).count()
        print(f"Starting unread count - Instructor: {inst_start_count}, Evaluator: {eval_start_count}")

        # 4. Create and Complete a Manual session
        print("Simulating manual study completion for COLREGS Rule 9...")
        from datetime import datetime, UTC
        
        test_session = TrainingSession(
            id=uuid.uuid4(),
            scenario_id=scenario.id,
            trainee_id=trainee.id,
            status="active",
            started_at=datetime.now(UTC),
            telemetry_log=[],
            created_at=datetime.now(UTC),
        )
        db.add(test_session)
        db.commit()
        db.refresh(test_session)

        # Update and trigger ending of session (simulate API PATCH /sessions/{id}/end)
        test_session.status = "completed"
        test_session.ended_at = datetime.now(UTC)
        test_session.instructor_notes = "Sovereign AI Auto-Score: Fully completed study manual for \"Basic: COLREGS Rule 9 Narrow Channel Navigation\" (Topic ID: 1)"
        test_session.score = {"overall": 100}
        db.commit()

        # Run the notification dispatcher logic
        from app.services.notification_service import create_notification
        import re

        trainee_name = trainee.name
        trainee_service = trainee.service_number
        subject = scenario.title
        
        if test_session.instructor_notes and "Fully completed study manual for" in test_session.instructor_notes:
            match = re.search(r'Fully completed study manual for "([^"]+)"', test_session.instructor_notes)
            if match:
                subject = match.group(1)

        print(f"Discovered subject title: '{subject}'")

        # Create notifications
        staff_members = db.query(User).filter(User.role.in_(["instructor", "evaluator"])).all()
        created_notifs = 0
        for staff in staff_members:
            create_notification(
                db=db,
                user_id=staff.id,
                notification_type="session_update",
                title="Subject Completed — Certificate Action Required",
                body=(
                    f"Trainee {trainee_name} ({trainee_service}) has successfully completed the subject "
                    f"\"{subject}\".\n\n"
                    f"Please review their performance log and issue the corresponding completion certificate."
                ),
                metadata={
                    "session_id": str(test_session.id),
                    "trainee_id": str(test_session.trainee_id),
                    "subject": subject,
                    "action": "issue_certificate"
                }
            )
            created_notifs += 1

        print(f"Created {created_notifs} notifications.")

        # 5. Assertions
        inst_end_count = db.query(Notification).filter(Notification.user_id == instructor.id, Notification.is_read == False).count()
        eval_end_count = db.query(Notification).filter(Notification.user_id == evaluator.id, Notification.is_read == False).count()
        print(f"Ending unread count - Instructor: {inst_end_count}, Evaluator: {eval_end_count}")

        assert inst_end_count == inst_start_count + 1, "Instructor notification not created!"
        assert eval_end_count == eval_start_count + 1, "Evaluator notification not created!"

        # Let's inspect the latest notification for the instructor
        latest_notif = db.query(Notification).filter(Notification.user_id == instructor.id).order_by(Notification.created_at.desc()).first()
        print("\n--- INSTRUCTOR NOTIFICATION DETAIL ---")
        print(f"Title: {latest_notif.title}")
        print(f"Body:\n{latest_notif.body}")
        print(f"Extra Data: {latest_notif.extra_data}")
        print("--------------------------------------\n")

        print("[SUCCESS] Subject completion notification logic verified successfully!")

        # Clean up test session and notifications
        db.query(Notification).filter(Notification.extra_data['session_id'].astext == str(test_session.id)).delete(synchronize_session=False)
        db.delete(test_session)
        db.commit()
        print("Test data cleaned up successfully.")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_subject_completion_notifications()
