import time
import pandas as pd
import json
import re
import logging
from functools import wraps
from inputs_handler import load_relatives
from routes import calculate_symmetric_distances, find_shortest_route
from modes import calculate_route_preferences, summarize_alternatives, display_alternatives
from visualization import visualize_geographical_network_with_lines
from geopy.distance import geodesic

# Import the logging setup from logging_config.py
from logging_config import setup_logging

# Configure logging using custom settings
setup_logging()

# Get the logger from the root logger defined in logging_config.py
logger = logging.getLogger()

# Decorator for performance logging
def log_execution_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.info(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

class RoutePlanner:
    def __init__(self):
        """
        Initialize the RoutePlanner class with Tarjan's home location, relatives, and transport modes.
        """
        logger.info("Initializing RoutePlanner...")

        # Step 1: Load Tarjan's home data from tarjan_home.json
        try:
            with open('data/tarjan_home.json', 'r') as file:
                self.tarjan_home = json.load(file)
                logger.info("Tarjan's home location loaded successfully.")
        except FileNotFoundError:
            logger.error("Tarjan's home file not found.")
            raise RuntimeError("Tarjan's home file is missing.")
        except json.JSONDecodeError:
            logger.error("Error decoding Tarjan's home JSON file.")
            raise RuntimeError("Tarjan's home file is corrupted or invalid.")

        # Step 2: Load relatives data
        try:
            self.relations = load_relatives()
            logger.info("Relatives data loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading relatives data: {e}")
            self.relations = []

        # Step 3: Load transport modes data
        try:
            with open('data/modes.json', 'r') as file:
                self.transport_modes = json.load(file)
                logger.info("Transport modes loaded successfully.")
        except FileNotFoundError:
            logger.error("Transport modes file not found.")
            raise RuntimeError("Transport modes file is missing.")
        except json.JSONDecodeError:
            logger.error("Error decoding transport modes JSON file.")
            raise RuntimeError("Transport modes file is corrupted or invalid.")

    @log_execution_time
    def generate_final_route_report(self, route_alternatives, distances, chosen_route):
        """
        Generate a CSV report summarizing the chosen route.
        """
        data = []
        total_time = 0
        total_cost = 0
        total_distance = 0
        num_mode_changes = 0
        last_mode = None

        for segment in chosen_route:
            from_location = segment['from']
            to_location = segment['to']
            selected_mode = segment["selected_mode"]

            distance = distances.get((from_location, to_location)) or distances.get((to_location, from_location))
            if not distance and from_location == "Home":
                distance = distances.get((from_location, to_location))
            elif not distance and to_location == "Home":
                distance = distances.get((from_location, to_location))

            total_time += selected_mode['total_time']
            total_cost += selected_mode['cost']
            total_distance += distance

            if selected_mode["mode"] != last_mode:
                num_mode_changes += 1
                last_mode = selected_mode["mode"]

            row = {
                "From → To": f"{from_location} → {to_location}",
                "Selected Mode": selected_mode["mode"],
                "Travel Time (min)": f"{selected_mode['travel_time']:.2f}",
                "Transfer Time (min)": f"{selected_mode['transfer_time']:.2f}",
                "Total Time (min)": f"{selected_mode['total_time']:.2f}",
                "Cost (Units)": f"{selected_mode['cost']:.2f}",
                "Distance (km)": f"{distance:.2f}"
            }
            data.append(row)

        total_row = {
            "From → To": "Total",
            "Selected Mode": "",
            "Travel Time (min)": f"{total_time:.2f}",
            "Transfer Time (min)": f"{total_time - total_distance:.2f}",
            "Total Time (min)": f"{total_time:.2f}",
            "Cost (Units)": f"{total_cost:.2f}",
            "Distance (km)": f"{total_distance:.2f}"
        }
        data.append(total_row)

        summary = {
            "Total Cost (Units)": f"{total_cost:.2f}",
            "Total Time (min)": f"{total_time:.2f}",
            "Total Distance (km)": f"{total_distance:.2f}",
            "Number of Mode Changes": num_mode_changes
        }

        df = pd.DataFrame(data)

        # Save the summary to a CSV file
        report_file = "final_route_report.csv"
        try:
            with open(report_file, 'w', newline='', encoding='utf-8') as file:
                file.write("🌟 Final Route Summary 🌟\n")
                file.write(f"Total Cost (Units): {summary['Total Cost (Units)']}\n")
                file.write(f"Total Time (min): {summary['Total Time (min)']}\n")
                file.write(f"Total Distance (km): {summary['Total Distance (km)']}\n")
                file.write(f"Number of Mode Changes: {summary['Number of Mode Changes']}\n")
                file.write("\n")
                df.to_csv(file, index=False)
            logger.info(f"Final route report saved to {report_file}")
        except IOError as e:
            logger.error(f"Error saving the route report: {e}")
            raise RuntimeError("Failed to save the final route report.")

        print("\n🌟 Final Route Summary 🌟")
        print(f"Total Cost: {summary['Total Cost (Units)']}")
        print(f"Total Time: {summary['Total Time (min)']} minutes")
        print(f"Total Distance: {summary['Total Distance (km)']} km")
        print(f"Number of Mode Changes: {summary['Number of Mode Changes']}")
        print("\nDetailed Route Information:")
        print(df.to_string(index=False))

        return summary, df

    def get_user_preference(self):
        """
        Get user preference for route optimization: least time, least cost, or balanced.
        """
        attempt_limit = 3
        attempts = 0
        while attempts < attempt_limit:
            print("1️⃣ **Least Time** – Optimize for the quickest route.")
            print("2️⃣ **Least Cost** – Optimize for the cheapest route.")
            print("3️⃣ **Balanced** – Find a balance between time and cost.")
            
            
            preference_choice = input("🚐 Enter your choice (1/2/3): ").strip()
            if re.match(r"^[1-3]$", preference_choice):
                return {"1": "least_time", "2": "least_cost", "3": "balanced_topsis"}[preference_choice]
            else:
                print("❌ Invalid input. Please enter 1, 2, or 3.")
                logger.warning(f"Invalid input: {preference_choice}")
                attempts += 1
                if attempts == attempt_limit:
                    print("❗ Maximum attempts reached. Exiting.")
                    exit()

    @log_execution_time
    def execute(self):
      """
    Execute the route planning process with a user-friendly and professional welcome message.
     """
    # Welcome message with icons for visual appeal and clarity
      print("\n✨ Welcome to **Tarjan's Route Planner**! ✨")
      print("🌟 Plan your journey efficiently with optimized routes based on your preferences.")
    
    # Brief explanation of what the system can do
      print("\n🔹 **What can you do?**")
      print("  - 🚀 Find the fastest route")
      print("  - 💰 Find the most cost-effective route")
      print("  - ⚖️ Balance time and cost for the best route")
    
    # Let the user know what to do next
      print("\n🔧 Please select your route optimization preference from the options below:")

    
    # Continue with the existing process
      distances = calculate_symmetric_distances(self.relations, self.tarjan_home)
      preference = self.get_user_preference()

      shortest_route = find_shortest_route(self.relations, distances, tarjan_home_name=self.tarjan_home["name"])
      selected_route = shortest_route["route"]

      route_alternatives = calculate_route_preferences(selected_route, distances, self.transport_modes, preference)
      summaries = summarize_alternatives(route_alternatives)

      if preference in ["least_time", "least_cost"]:
          display_alternatives([summaries[0]], preference)
          chosen_route = route_alternatives[0]
      else:
          selected_index = display_alternatives(summaries)
          chosen_route = route_alternatives[selected_index]

      print(f"\n🌟 Visualizing Selected Alternative 🌟")
      visualize_geographical_network_with_lines(self.relations, chosen_route, tarjan_home=self.tarjan_home)

      print("\n📊 Generating route summary...")
      self.generate_final_route_report(route_alternatives, distances, chosen_route=chosen_route)

if __name__ == "__main__":
    route_planner = RoutePlanner()
    route_planner.execute()
