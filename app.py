import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import plotly.express as px
import plotly.graph_objects as go
import os
import json
from uuid import uuid4

# Files for data storage
TASKS_FILE = "task_log.csv"
HABITS_FILE = "habits.json"
TODO_FILE = "todo.csv"
REWARDS_FILE = "rewards.json"  # Add this line

# Initialize files if they don't exist
if not os.path.exists(TASKS_FILE):
    df_init = pd.DataFrame(columns=["Date", "Category", "Task", "Points", "Comment"])
    df_init.to_csv(TASKS_FILE, index=False)

if not os.path.exists(TODO_FILE):
    todo_init = pd.DataFrame(columns=["ID", "Task", "Due Date", "Priority", "Status", "Points"])
    todo_init.to_csv(TODO_FILE, index=False)

if not os.path.exists(HABITS_FILE):
    habits_init = {
        "habits": [
            {"name": "Daily Coding", "category": "Professional", "points": 5},
            {"name": "LinkedIn Post", "category": "Professional", "points": 10},
            {"name": "Job Application", "category": "Professional", "points": 15},
            {"name": "Exercise", "category": "Personal", "points": 5},
            {"name": "Reading", "category": "Personal", "points": 3}
        ]
    }
    with open(HABITS_FILE, "w") as f:
        json.dump(habits_init, f, indent=4)

# Initialize the rewards file
if not os.path.exists(REWARDS_FILE):
    rewards_init = {
        "rewards": [
            {"id": str(uuid4()), "name": "Coffee Shop Visit", "description": "Treat yourself to a nice coffee", "points_required": 50, "category": "Small Treat", "redeemed": False},
            {"id": str(uuid4()), "name": "Movie Night", "description": "Watch that movie you've been wanting to see", "points_required": 100, "category": "Entertainment", "redeemed": False},
            {"id": str(uuid4()), "name": "New Book", "description": "Buy that book from your wishlist", "points_required": 200, "category": "Learning", "redeemed": False}
        ],
        "redeemed_history": []
    }
    with open(REWARDS_FILE, "w") as f:
        json.dump(rewards_init, f, indent=4)

# Load existing data
tasks_df = pd.read_csv(TASKS_FILE)
todo_df = pd.read_csv(TODO_FILE)

with open(HABITS_FILE, "r") as f:
    habits_data = json.load(f)

# Page layout
st.set_page_config(page_title="RaízXP | Gamification Tracker", layout="wide")

# Sidebar navigation
st.sidebar.title("🎮 RaízXP")
page = st.sidebar.radio("Navigation", ["Dashboard", "Log Activity", "Manage Habits", "To-Do List", "Rewards", "Analytics"])

# Helper functions
def load_task_data():
    try:
        df = pd.read_csv("task_log.csv")
        required_columns = ["Date", "Category", "Task", "Points", "Comment"]
        if not all(col in df.columns for col in required_columns):
            st.error("Invalid CSV format: Missing required columns")
            return pd.DataFrame(columns=required_columns)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "Category", "Task", "Points", "Comment"])
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(columns=["Date", "Category", "Task", "Points", "Comment"])

def load_data():
    """Reload all data sources"""
    tasks_df = pd.read_csv(TASKS_FILE)
    todo_df = pd.read_csv(TODO_FILE)
    with open(HABITS_FILE, "r") as f:
        habits_data = json.load(f)
    with open(REWARDS_FILE, "r") as f:
        rewards_data = json.load(f)
    return tasks_df, todo_df, habits_data, rewards_data

def calculate_available_points():
    """Calculate available points (total minus redeemed)"""
    tasks_df = pd.read_csv(TASKS_FILE)
    total_earned = tasks_df["Points"].sum() if not tasks_df.empty else 0
    
    with open(REWARDS_FILE, "r") as f:
        rewards_data = json.load(f)
    
    redeemed_points = sum(item["points_required"] for item in rewards_data["redeemed_history"])
    
    return total_earned - redeemed_points

# Dashboard page
if page == "Dashboard":
    st.title("🎯 RaízXP - Personal Gamification Tracker")
    
    # Load the latest data
    tasks_df, todo_df, habits_data, rewards_data = load_data()
    
    # Calculate metrics
    total_points = tasks_df["Points"].sum() if not tasks_df.empty else 0
    if not tasks_df.empty:
        tasks_this_week = tasks_df[tasks_df["Date"] >= (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")]
        points_this_week = tasks_this_week["Points"].sum()
        
        # Get professional vs personal split
        category_split = tasks_df.groupby("Category")["Points"].sum()
        professional_points = category_split.get("Professional", 0)
        personal_points = category_split.get("Personal", 0)
    else:
        points_this_week = 0
        professional_points = 0
        personal_points = 0
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Points", total_points)
    with col2:
        st.metric("Points This Week", points_this_week)
    with col3:
        st.metric("Tasks Completed", len(tasks_df))
    
    # Display category breakdown
    st.subheader("Points by Category")
    category_col1, category_col2 = st.columns(2)
    with category_col1:
        st.metric("Professional", professional_points)
    with category_col2:
        st.metric("Personal", personal_points)
    
    # Recent activities
    st.subheader("Recent Activities")
    if not tasks_df.empty:
        st.dataframe(tasks_df.sort_values(by="Date", ascending=False).head(5), use_container_width=True)
    else:
        st.info("No activities logged yet. Start by adding some in the 'Log Activity' section!")
    
    # Pending to-do items
    st.subheader("Pending To-Do Items")
    if not todo_df.empty:
        pending_tasks = todo_df[todo_df["Status"] != "Completed"].sort_values(by="Priority", ascending=True)
        if not pending_tasks.empty:
            st.dataframe(pending_tasks[["Task", "Due Date", "Priority", "Points"]], use_container_width=True)
        else:
            st.success("No pending tasks! You're all caught up.")
    else:
        st.info("No to-do items yet. Add some in the 'To-Do List' section!")

# Log Activity page
elif page == "Log Activity":
    st.title("📝 Log Your Activity")
    
    tasks_df, todo_df, habits_data, rewards_data = load_data()
    
    # Create tabs for quick log vs. custom log
    log_tab1, log_tab2 = st.tabs(["Quick Log", "Custom Activity"])
    
    with log_tab1:
        st.subheader("Quick Log from Habits")
        
        with st.form(key="quick_log_form"):
            date = st.date_input("Date", datetime.date.today())
            
            # Group habits by category for the selectbox
            habits_by_category = {}
            for habit in habits_data["habits"]:
                category = habit["category"]
                if category not in habits_by_category:
                    habits_by_category[category] = []
                habits_by_category[category].append(f"{habit['name']} ({habit['points']} pts)")
            
            selected_category = st.selectbox("Category", list(habits_by_category.keys()))
            selected_habit_with_points = st.selectbox("Select Habit", habits_by_category[selected_category])
            
            # Extract habit name and points
            habit_name = selected_habit_with_points.split(" (")[0]
            habit_points = int(selected_habit_with_points.split("(")[1].split(" ")[0])
            
            comment = st.text_area("Comment (optional)", key="quick_comment")
            quick_submit = st.form_submit_button("Log Activity")
        
        if quick_submit:
            new_row = pd.DataFrame([[date.strftime("%Y-%m-%d"), selected_category, habit_name, habit_points, comment]],
                                   columns=["Date", "Category", "Task", "Points", "Comment"])
            updated_tasks_df = pd.concat([tasks_df, new_row], ignore_index=True)
            updated_tasks_df.to_csv(TASKS_FILE, index=False)
            st.success(f"✅ Activity logged: {habit_name} for {habit_points} points!")
            
            # Refresh data
            tasks_df = pd.read_csv(TASKS_FILE)
    
    with log_tab2:
        st.subheader("Log Custom Activity")
        
        with st.form(key="custom_log_form"):
            c_date = st.date_input("Date", datetime.date.today(), key="custom_date")
            c_category = st.selectbox("Category", ["Professional", "Personal"], key="custom_category")
            c_task = st.text_input("Activity Description", key="custom_task")
            c_points = st.number_input("Points", min_value=1, max_value=100, value=5, step=1, key="custom_points")
            c_comment = st.text_area("Comment (optional)", key="custom_comment")
            custom_submit = st.form_submit_button("Log Custom Activity")
        
        if custom_submit:
            if not c_task:
                st.error("Please enter an activity description.")
            else:
                new_row = pd.DataFrame([[c_date.strftime("%Y-%m-%d"), c_category, c_task, c_points, c_comment]],
                                       columns=["Date", "Category", "Task", "Points", "Comment"])
                updated_tasks_df = pd.concat([tasks_df, new_row], ignore_index=True)
                updated_tasks_df.to_csv(TASKS_FILE, index=False)
                st.success(f"✅ Custom activity logged: {c_task} for {c_points} points!")
                
                # Refresh data
                tasks_df = pd.read_csv(TASKS_FILE)
    
    # Activity History
    st.subheader("Activity History")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        category_options = ["All"] + list(tasks_df["Category"].unique()) if not tasks_df.empty else ["All"]
        filter_category = st.multiselect("Filter by Category", 
                                        options=category_options,
                                        default="All")
    with col2:
        date_range = st.date_input("Date Range",
                                  value=(datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()),
                                  max_value=datetime.date.today())
    
    # Apply filters
    filtered_df = tasks_df.copy()
    if filter_category and "All" not in filter_category:
        filtered_df = filtered_df[filtered_df["Category"].isin(filter_category)]

    if len(date_range) == 2 and not filtered_df.empty:
        start_date, end_date = date_range
        filtered_df = filtered_df[(filtered_df["Date"] >= start_date.strftime("%Y-%m-%d")) & 
                                 (filtered_df["Date"] <= end_date.strftime("%Y-%m-%d"))]
    
    # Show filtered results
    if not filtered_df.empty:
        st.dataframe(filtered_df.sort_values(by="Date", ascending=False), use_container_width=True)
    else:
        st.info("No activities match your filter criteria.")

# Manage Habits page
elif page == "Manage Habits":
    st.title("⚙️ Manage Your Habits")
    
    tasks_df, todo_df, habits_data, rewards_data = load_data()
    
    # Display existing habits
    st.subheader("Your Current Habits")
    
    # Create a DataFrame for better display
    habits_display_df = pd.DataFrame(habits_data["habits"])
    if not habits_display_df.empty:
        st.dataframe(habits_display_df, use_container_width=True)
    
    # Add new habit
    st.subheader("Add New Habit")
    with st.form(key="add_habit_form"):
        habit_name = st.text_input("Habit Name")
        habit_category = st.selectbox("Category", ["Professional", "Personal"])
        habit_points = st.number_input("Points", min_value=1, max_value=100, value=5, step=1)
        add_habit_submit = st.form_submit_button("Add Habit")
    
    if add_habit_submit:
        if not habit_name:
            st.error("Please enter a habit name.")
        else:
            new_habit = {
                "name": habit_name,
                "category": habit_category,
                "points": habit_points
            }
            habits_data["habits"].append(new_habit)
            
            with open(HABITS_FILE, "w") as f:
                json.dump(habits_data, f, indent=4)
            
            st.success(f"✅ New habit added: {habit_name}")
            
            # Refresh data
            with open(HABITS_FILE, "r") as f:
                habits_data = json.load(f)
    
    # Edit/Remove habits
    st.subheader("Edit or Remove Habits")
    
    if habits_data["habits"]:
        habit_to_edit = st.selectbox("Select Habit to Edit/Remove", 
                                   options=[f"{h['name']} ({h['category']}, {h['points']} pts)" for h in habits_data["habits"]])
        
        # Find the selected habit
        selected_index = -1
        for i, habit in enumerate(habits_data["habits"]):
            if f"{habit['name']} ({habit['category']}, {habit['points']} pts)" == habit_to_edit:
                selected_index = i
                break
        
        if selected_index >= 0:
            selected_habit = habits_data["habits"][selected_index]
            
            col1, col2 = st.columns(2)
            with col1:
                # Edit form
                with st.form(key="edit_habit_form"):
                    edit_name = st.text_input("Habit Name", value=selected_habit["name"])
                    edit_category = st.selectbox("Category", ["Professional", "Personal"], 
                                               index=0 if selected_habit["category"] == "Professional" else 1)
                    edit_points = st.number_input("Points", min_value=1, max_value=100, 
                                                value=selected_habit["points"], step=1)
                    update_habit = st.form_submit_button("Update Habit")
                
                if update_habit:
                    habits_data["habits"][selected_index] = {
                        "name": edit_name,
                        "category": edit_category,
                        "points": edit_points
                    }
                    
                    with open(HABITS_FILE, "w") as f:
                        json.dump(habits_data, f, indent=4)
                    
                    st.success("✅ Habit updated successfully!")
                    
                    # Refresh data
                    with open(HABITS_FILE, "r") as f:
                        habits_data = json.load(f)
            
            with col2:
                # Remove option
                st.write("Remove this habit")
                if st.button("Delete Habit", key="delete_habit"):
                    habits_data["habits"].pop(selected_index)
                    
                    with open(HABITS_FILE, "w") as f:
                        json.dump(habits_data, f, indent=4)
                    
                    st.success("✅ Habit removed successfully!")
                    
                    # Refresh data
                    with open(HABITS_FILE, "r") as f:
                        habits_data = json.load(f)

# To-Do List page
elif page == "To-Do List":
    st.title("📋 To-Do List")
    
    tasks_df, todo_df, habits_data, rewards_data = load_data()
    
    # Create a new todo item
    st.subheader("Add New To-Do Item")
    with st.form(key="add_todo_form"):
        todo_task = st.text_input("Task Description")
        col1, col2 = st.columns(2)
        with col1:
            due_date = st.date_input("Due Date", datetime.date.today() + datetime.timedelta(days=1))
        with col2:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        
        todo_points = st.number_input("Completion Points", min_value=1, max_value=100, value=10, step=1)
        add_todo_submit = st.form_submit_button("Add To-Do Item")
    
    if add_todo_submit:
        if not todo_task:
            st.error("Please enter a task description.")
        else:
            new_todo = pd.DataFrame([[str(uuid4()), todo_task, due_date.strftime("%Y-%m-%d"), priority, "Pending", todo_points]],
                                   columns=["ID", "Task", "Due Date", "Priority", "Status", "Points"])
            todo_df = pd.concat([todo_df, new_todo], ignore_index=True)
            todo_df.to_csv(TODO_FILE, index=False)
            st.success(f"✅ New to-do item added: {todo_task}")
            
            # Refresh data
            todo_df = pd.read_csv(TODO_FILE)
    
    # Display and manage todo items
    st.subheader("Your To-Do List")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed"], index=0)
    with col2:
        priority_filter = st.multiselect("Priority", ["All", "High", "Medium", "Low"], default="All")
    
    # Apply filters
    filtered_todo = todo_df.copy()
    if status_filter != "All":
        filtered_todo = filtered_todo[filtered_todo["Status"] == status_filter]
    
    if priority_filter and "All" not in priority_filter:
        filtered_todo = filtered_todo[filtered_todo["Priority"].isin(priority_filter)]
    
    # Display filtered todo items
    if not filtered_todo.empty:
        for _, row in filtered_todo.sort_values(by=["Priority", "Due Date"]).iterrows():
            task_id = row["ID"]
            task = row["Task"]
            due_date = row["Due Date"]
            priority = row["Priority"]
            status = row["Status"]
            points = row["Points"]
            
            # Create color code based on priority
            priority_color = {
                "High": "🔴",
                "Medium": "🟠",
                "Low": "🟢"
            }
            
            # Create todo item card
            with st.container():
                col1, col2, col3 = st.columns([6, 2, 2])
                
                with col1:
                    st.write(f"**{task}** {priority_color.get(priority, '')}")
                    st.caption(f"Due: {due_date} | Status: {status} | Points: {points}")
                
                with col2:
                    if status != "Completed":
                        if st.button("Mark Complete", key=f"complete_{task_id}"):
                            # Update status to completed
                            todo_df.loc[todo_df["ID"] == task_id, "Status"] = "Completed"
                            todo_df.to_csv(TODO_FILE, index=False)
                            
                            # Log the completed task as an activity
                            new_activity = pd.DataFrame([
                                [datetime.date.today().strftime("%Y-%m-%d"), 
                                 "Personal", 
                                 f"Completed: {task}", 
                                 points, 
                                 f"Completed to-do item: {task}"]
                            ], columns=["Date", "Category", "Task", "Points", "Comment"])
                            
                            tasks_df = pd.concat([tasks_df, new_activity], ignore_index=True)
                            tasks_df.to_csv(TASKS_FILE, index=False)
                            
                            st.success(f"✅ Task completed: {task} (+{points} points)")
                            st.experimental_rerun()
                
                with col3:
                    if st.button("Remove", key=f"remove_{task_id}"):
                        todo_df = todo_df[todo_df["ID"] != task_id]
                        todo_df.to_csv(TODO_FILE, index=False)
                        st.success(f"✅ Task removed: {task}")
                        st.experimental_rerun()
                
                st.markdown("---")
    else:
        st.info("No to-do items match your filter criteria.")

# Rewards page
elif page == "Rewards":
    st.title("🎁 Rewards")
    
    tasks_df, todo_df, habits_data, rewards_data = load_data()
    
    # Calculate available points
    available_points = calculate_available_points()
    
    # Display current points and progress
    st.header("Your Points")
    col1, col2 = st.columns(2)
    with col1:
        
        # Get unredeemed rewards
        unredeemed_rewards = [r for r in rewards_data["rewards"] if not r["redeemed"]]
        
        if unredeemed_rewards:
            # Sort by points required
            unredeemed_rewards.sort(key=lambda x: x["points_required"])
            
            # Create a grid layout for rewards
            for i in range(0, len(unredeemed_rewards), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i+j < len(unredeemed_rewards):
                        reward = unredeemed_rewards[i+j]
                        with cols[j]:
                            st.markdown(f"### 🎁 {reward['name']}")
                            st.markdown(f"**{reward['points_required']} points**")
                            st.markdown(f"*{reward['description']}*")
                            st.markdown(f"*Category: {reward['category']}*")
                            
                            # Visual progress bar
                            progress = min(1.0, available_points / reward["points_required"])
                            st.progress(progress)
                            st.text(f"{available_points}/{reward['points_required']} points")
                            
                            # Redeem button - enabled only if enough points
                            if available_points >= reward["points_required"]:
                                if st.button("Redeem Reward", key=f"redeem_{reward['id']}"):
                                    # Move to redeemed history with timestamp
                                    rewards_data["redeemed_history"].append({
                                        "reward_id": reward["id"],
                                        "name": reward["name"],
                                        "points_cost": reward["points_required"],
                                        "redeemed_on": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    })
                                    # Mark as redeemed
                                    for r in rewards_data["rewards"]:
                                        if r["id"] == reward["id"]:
                                            r["redeemed"] = True
                                            break
                                    
                                    # Save updated rewards data
                                    with open(REWARDS_FILE, "w") as f:
                                        json.dump(rewards_data, f, indent=4)
                                    
                                    st.balloons()
                                    st.success(f"🎉 You've redeemed '{reward['name']}'! Enjoy your reward!")
                                    st.experimental_rerun()
                            else:
                                st.button("Not Enough Points", disabled=True, key=f"disabled_{reward['id']}")
                            
                            st.markdown("---")
        else:
            st.info("No rewards available. Add some in the 'Add New Reward' tab!")
    
    with reward_tab2:
        st.subheader("Create a New Reward")
        
        with st.form("add_reward_form"):
            reward_name = st.text_input("Reward Name")
            reward_desc = st.text_area("Description")
            reward_points = st.number_input("Points Required", min_value=1, value=50, step=5)
            reward_category = st.selectbox("Category", [
                "Small Treat", "Entertainment", "Learning", "Self-Care", 
                "Gaming", "Shopping", "Social", "Excursion", "Lazy Day", "Custom"
            ])
            
            if reward_category == "Custom":
                custom_category = st.text_input("Enter Custom Category")
            
            submit_reward = st.form_submit_button("Add Reward")
        
        if submit_reward:
            if not reward_name:
                st.error("Please enter a reward name.")
            else:
                # Create new reward
                new_reward = {
                    "id": str(uuid4()),
                    "name": reward_name,
                    "description": reward_desc,
                    "points_required": reward_points,
                    "category": custom_category if reward_category == "Custom" else reward_category,
                    "redeemed": False
                }
                
                # Add to rewards list
                rewards_data["rewards"].append(new_reward)
                
                # Save updated rewards
                with open(REWARDS_FILE, "w") as f:
                    json.dump(rewards_data, f, indent=4)
                
                st.success(f"✅ New reward added: {reward_name}")
                
                # Refresh data
                with open(REWARDS_FILE, "r") as f:
                    rewards_data = json.load(f)
    
    with reward_tab3:
        st.subheader("Redemption History")
        
        if rewards_data["redeemed_history"]:
            # Convert to DataFrame for better display
            history_df = pd.DataFrame(rewards_data["redeemed_history"])
            history_df = history_df.rename(columns={
                "name": "Reward",
                "points_cost": "Points Cost",
                "redeemed_on": "Redeemed On"
            })
            
            st.dataframe(history_df[["Reward", "Points Cost", "Redeemed On"]].sort_values(
                by="Redeemed On", ascending=False), use_container_width=True)
        else:
            st.info("No rewards have been redeemed yet.")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("RaízXP - Personal Gamification Tracker")
st.sidebar.caption("Designed for non-traditional paths and independent learners")
st.sidebar.caption("© 2025 Gabriel Felipe Fernandes Pinheiro")