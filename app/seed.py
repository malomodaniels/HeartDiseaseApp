from datetime import datetime
from . import db
from .models import SensitizationPost  # adjust import to your actual model name

def seed_sensitization_posts():
    # Avoid duplicating seed data
    if SensitizationPost.query.first():
        return

    posts = [
        SensitizationPost(
            title="Heart Disease: The Basics",
            summary="Understand what heart disease is, common causes, and how risk builds over time.",
            content=(
                "Heart disease is an umbrella term for conditions affecting the heart and blood vessels. "
                "Key drivers include high blood pressure, high cholesterol, smoking, diabetes, obesity, and inactivity. "
                "The good news: many risk factors are modifiable with consistent lifestyle changes and routine check-ups."
            ),
            image_path="images/sensitization/heart_basics.jpg",
            category="Heart Health",
            created_at=datetime.utcnow(),
            is_published=True,
        ),
        SensitizationPost(
            title="Know Your Blood Pressure Numbers",
            summary="High blood pressure often has no symptoms—learn the ranges and what to do.",
            content=(
                "Blood pressure is written as systolic/diastolic (e.g., 120/80). "
                "If your readings are frequently high, talk to a clinician. "
                "Reduce salt, manage stress, exercise regularly, and take medications as prescribed."
            ),
            image_path="images/sensitization/bp_control.jpg",
            category="Prevention",
            created_at=datetime.utcnow(),
            is_published=True,
        ),
        SensitizationPost(
            title="Stroke Warning Signs (FAST)",
            summary="Recognize stroke symptoms early—quick action can save life and function.",
            content=(
                "FAST: Face drooping, Arm weakness, Speech difficulty, Time to call emergency services. "
                "Do not wait for symptoms to resolve. Rapid treatment improves outcomes."
            ),
            image_path="images/sensitization/stroke_signs.jpg",
            category="Emergency",
            created_at=datetime.utcnow(),
            is_published=True,
        ),
        SensitizationPost(
            title="Reduce Salt & Sugar: Simple Swaps",
            summary="Small daily swaps can significantly improve long-term cardiovascular risk.",
            content=(
                "Use herbs/spices instead of extra salt. Choose water over sugary drinks. "
                "Read food labels: many processed foods hide salt and added sugar."
            ),
            image_path="images/sensitization/salt_sugar.jpg",
            category="Nutrition",
            created_at=datetime.utcnow(),
            is_published=True,
        ),
        SensitizationPost(
            title="Exercise That Protects the Heart",
            summary="You don’t need a gym—consistency matters more than intensity.",
            content=(
                "Aim for at least 150 minutes of moderate activity weekly (brisk walking counts). "
                "Start small: 10–15 minutes daily and build gradually."
            ),
            image_path="images/sensitization/exercise.jpg",
            category="Lifestyle",
            created_at=datetime.utcnow(),
            is_published=True,
        ),
        SensitizationPost(
            title="When to Seek Care Immediately",
            summary="Know the red flags that require urgent medical attention.",
            content=(
                "Seek urgent help for chest pain/pressure, sudden shortness of breath, fainting, "
                "one-sided weakness, or severe sudden headache. "
                "Do not self-medicate or wait it out."
            ),
            image_path="images/sensitization/warning_signs.jpg",
            category="Safety",
            created_at=datetime.utcnow(),
            is_published=True,
        ),
    ]

    db.session.add_all(posts)
    db.session.commit()
