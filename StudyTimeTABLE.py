import tkinter as tk
from tkinter import messagebox, scrolledtext
import datetime
import json
import os

DATA_FILE = "study_planner.json"

# -------------------- DATA LAYER --------------------

class UserProfile:
    def __init__(self, name, class_level, subjects, study_period):
        self.name = name
        self.class_level = class_level
        self.subjects = subjects
        self.study_period = study_period  # minutes


class DailyPlan:
    def __init__(self, date):
        self.date = date
        self.weak_areas = []
        self.goals = []
        self.take_test = False
        self.completed = False


class StudyPlanner:
    def __init__(self, profile):
        self.profile = profile
        self.daily_plans = {}

    def generate_schedule(self, date):
        plan = self.daily_plans.get(date)
        if not plan:
            return "No plan available for today."

        activities = []

        for wa in plan.weak_areas:
            activities.append(f"Revise weak area: {wa}")

        for sub in self.profile.subjects:
            activities.append(f"Study {sub} (NCERT + Practice)")

        for goal in plan.goals:
            activities.append(f"Goal: {goal}")

        if plan.take_test:
            activities.append("Attempt Mock Test")

        if not activities:
            return "No activities planned."

        minutes_each = max(20, self.profile.study_period // len(activities))
        start_time = datetime.datetime.combine(date, datetime.time(9, 0))

        schedule = []
        for act in activities:
            end_time = start_time + datetime.timedelta(minutes=minutes_each)
            schedule.append(
                f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} | {act}"
            )
            start_time = end_time

        return "\n".join(schedule)

    def save(self):
        data = {
            "profile": vars(self.profile),
            "daily_plans": {
                str(k): {
                    "weak_areas": v.weak_areas,
                    "goals": v.goals,
                    "take_test": v.take_test,
                    "completed": v.completed
                } for k, v in self.daily_plans.items()
            }
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls):
        if not os.path.exists(DATA_FILE):
            return None

        with open(DATA_FILE) as f:
            data = json.load(f)

        p = data["profile"]
        profile = UserProfile(
            p["name"], p["class_level"], p["subjects"], p["study_period"]
        )
        planner = cls(profile)

        for k, v in data["daily_plans"].items():
            date = datetime.date.fromisoformat(k)
            dp = DailyPlan(date)
            dp.weak_areas = v["weak_areas"]
            dp.goals = v["goals"]
            dp.take_test = v["take_test"]
            dp.completed = v["completed"]
            planner.daily_plans[date] = dp

        return planner


# -------------------- GUI --------------------

class StudyPlannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CBSE Study Planner")
        self.root.geometry("750x620")

        self.planner = StudyPlanner.load()
        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="CBSE STUDY PLANNER",
                 font=("Arial", 16, "bold")).pack(pady=10)

        # -------- PROFILE --------
        profile = tk.LabelFrame(self.root, text="User Profile",
                                font=("Arial", 11, "bold"), padx=10, pady=10)
        profile.pack(fill="x", padx=15)

        tk.Label(profile, text="Name").grid(row=0, column=0, sticky="w")
        self.name = tk.Entry(profile, width=30)
        self.name.grid(row=0, column=1, padx=10)

        tk.Label(profile, text="Class").grid(row=1, column=0, sticky="w")
        self.class_var = tk.StringVar(value="Class 6")
        tk.OptionMenu(profile, self.class_var,
                      *[f"Class {i}" for i in range(6, 13)]).grid(row=1, column=1, sticky="w")

        tk.Label(profile, text="Study Period (minutes)").grid(row=2, column=0, sticky="w")
        self.period_var = tk.StringVar(value="60")
        tk.OptionMenu(profile, self.period_var, "30", "60", "90", "120").grid(row=2, column=1, sticky="w")

        tk.Label(profile, text="Subjects (comma separated)").grid(row=3, column=0, sticky="w")
        self.subjects = tk.Entry(profile, width=30)
        self.subjects.grid(row=3, column=1, padx=10)

        # -------- DAILY --------
        daily = tk.LabelFrame(self.root, text="Daily Planning",
                              font=("Arial", 11, "bold"), padx=10, pady=10)
        daily.pack(fill="x", padx=15, pady=5)

        tk.Label(daily, text="Weak Areas").grid(row=0, column=0, sticky="w")
        self.weak = tk.Entry(daily, width=30)
        self.weak.grid(row=0, column=1, padx=10)

        tk.Label(daily, text="Goals").grid(row=1, column=0, sticky="w")
        self.goals = tk.Entry(daily, width=30)
        self.goals.grid(row=1, column=1, padx=10)

        self.test_var = tk.BooleanVar()
        tk.Checkbutton(daily, text="Include Mock Test",
                       variable=self.test_var).grid(row=2, column=1, sticky="w")

        # -------- BUTTONS --------
        btns = tk.Frame(self.root)
        btns.pack(pady=10)

        tk.Button(btns, text="Save Profile", width=18,
                  command=self.save_profile).grid(row=0, column=0, padx=5)

        tk.Button(btns, text="Plan Today", width=18,
                  command=self.plan_today).grid(row=0, column=1, padx=5)

        tk.Button(btns, text="Generate Schedule", width=18,
                  command=self.generate).grid(row=0, column=2, padx=5)

        tk.Button(btns, text="Mark Completed", width=18,
                  command=self.mark_completed).grid(row=0, column=3, padx=5)

        # -------- OUTPUT --------
        out_frame = tk.LabelFrame(self.root, text="Study Schedule",
                                  font=("Arial", 11, "bold"))
        out_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.output = scrolledtext.ScrolledText(
            out_frame, font=("Consolas", 10))
        self.output.pack(fill="both", expand=True)

    # -------- LOGIC --------

    def save_profile(self):
        try:
            name = self.name.get().strip()
            subjects = [s.strip() for s in self.subjects.get().split(",")]
            if not name or not subjects:
                raise ValueError

            profile = UserProfile(
                name,
                self.class_var.get(),
                subjects,
                int(self.period_var.get())
            )
            self.planner = StudyPlanner(profile)
            self.planner.save()
            messagebox.showinfo("Saved", "Profile saved successfully")
        except:
            messagebox.showerror("Error", "Invalid input")

    def plan_today(self):
        if not self.planner:
            return

        today = datetime.date.today()
        dp = DailyPlan(today)
        dp.weak_areas = [w.strip() for w in self.weak.get().split(",")]
        dp.goals = [g.strip() for g in self.goals.get().split(",")]
        dp.take_test = self.test_var.get()

        self.planner.daily_plans[today] = dp
        self.planner.save()
        messagebox.showinfo("Saved", "Today's plan saved")

    def generate(self):
        if not self.planner:
            return

        today = datetime.date.today()
        routine = self.planner.generate_schedule(today)
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, routine)

    def mark_completed(self):
        today = datetime.date.today()
        if today in self.planner.daily_plans:
            self.planner.daily_plans[today].completed = True
            self.planner.save()
            messagebox.showinfo("Done", "Today's plan marked as completed")


# -------------------- MAIN --------------------

def main():
    root = tk.Tk()
    StudyPlannerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
