import numpy as np
import logging
# Utility Functions

def calculate_mode_details(from_node, to_node, distance, transport_modes):
    """
    Calculate travel details for each transport mode between two nodes.
    """
    try:
        logging.info(f"Calculating mode details from {from_node} to {to_node} with distance {distance} km.")
        mode_details = []
        for mode in transport_modes:
            try:
                travel_time = (distance / mode["speed_kmh"]) * 60  # Convert hours to minutes
                transfer_time = mode["transfer_time_min"]
                total_time = travel_time + transfer_time  # Total time includes travel + transfer time
                cost = distance * mode["cost_per_km"]

                mode_details.append({
                    "mode": mode["mode"],
                    "travel_time": travel_time,
                    "transfer_time": transfer_time,
                    "total_time": total_time,
                    "cost": cost
                })
            except KeyError as e:
                logging.error(f"Missing key in mode data: {e}")
                raise
            except Exception as e:
                logging.error(f"Error calculating mode details for {from_node} to {to_node}: {e}")
                raise
        logging.debug(f"Calculated mode details: {mode_details}")
        return mode_details
    except Exception as e:
        logging.error(f"Error in calculate_mode_details: {e}")
        raise

# TOPSIS Evaluation for Balanced Route

def topsis_evaluation(mode_details, time_weight, cost_weight):
    """
    Use TOPSIS to evaluate the balanced preference and return the top modes.
    """
    try:
        logging.info(f"Evaluating modes using TOPSIS with time weight: {time_weight} and cost weight: {cost_weight}")
        # Extract total times and costs from the mode details
        total_times = np.array([mode["total_time"] for mode in mode_details])
        costs = np.array([mode["cost"] for mode in mode_details])

        # Normalize time and cost values using vector normalization
        norm_times = total_times / np.sqrt(np.sum(total_times ** 2))
        norm_costs = costs / np.sqrt(np.sum(costs ** 2))

        # Calculate the weighted normalized decision matrix
        weighted_times = norm_times * time_weight
        weighted_costs = norm_costs * cost_weight

        # Ideal (best) and anti-ideal (worst) solutions
        ideal_solution = [np.min(weighted_times), np.min(weighted_costs)]
        anti_ideal_solution = [np.max(weighted_times), np.max(weighted_costs)]

        # Calculate distance from ideal and anti-ideal solutions
        distances_to_ideal = np.sqrt((weighted_times - ideal_solution[0]) ** 2 + (weighted_costs - ideal_solution[1]) ** 2)
        distances_to_anti_ideal = np.sqrt((weighted_times - anti_ideal_solution[0]) ** 2 + (weighted_costs - anti_ideal_solution[1]) ** 2)

        # Calculate the TOPSIS score (closeness coefficient)
        topsis_scores = distances_to_anti_ideal / (distances_to_ideal + distances_to_anti_ideal + 1e-6)

        # Sort scores in descending order to get the best alternatives
        top_indices = np.argsort(topsis_scores)[::-1]

        # Select the top modes based on TOPSIS score
        top_modes = [mode_details[i] for i in top_indices]
        logging.debug(f"TOPSIS evaluation results: {top_modes}")
        return top_modes
    except Exception as e:
        logging.error(f"Error in topsis_evaluation: {e}")
        raise

# Route Calculation Functions

def calculate_route_preferences(route, distances, transport_modes, preference):
    """
    Evaluate all segments in the route and select the best mode for each segment based on user preference.
    Preferences can be "least_time", "least_cost", or "balanced_topsis".
    """
    try:
        logging.info(f"Calculating route preferences for route {route} with preference {preference}.")
        if preference == "balanced_topsis":
            return calculate_balanced_route(route, distances, transport_modes)
        elif preference == "least_time":
            return generate_single_route(route, distances, transport_modes, preference)
        elif preference == "least_cost":
            return generate_single_route(route, distances, transport_modes, preference)
        else:
            raise ValueError("Invalid preference. Choose from 'least_time', 'least_cost', or 'balanced_topsis'.")
    except ValueError as e:
        logging.error(f"Invalid preference: {e}")
        raise
    except Exception as e:
        logging.error(f"Error in calculate_route_preferences: {e}")
        raise

def generate_single_route(route, distances, transport_modes, preference):
    """
    Generate a single full route for least time or least cost, with multiple alternatives.
    """
    try:
        logging.info(f"Generating single route for preference: {preference}.")
        all_alternatives = []

        for i in range(3):  # Generate three distinct alternatives
            route_segments = []

            for j in range(len(route) - 1):
                from_node = route[j]
                to_node = route[j + 1]
                distance = distances[(from_node, to_node)]

                # Evaluate transport modes for the segment based on user preference
                mode_details = calculate_mode_details(from_node, to_node, distance, transport_modes)

                if preference == "least_time":
                    # Sort modes by travel time
                    sorted_modes = sorted(mode_details, key=lambda x: (x["total_time"], x["cost"]))
                elif preference == "least_cost":
                    # Sort modes by cost
                    sorted_modes = sorted(mode_details, key=lambda x: (x["cost"], x["total_time"]))
                else:
                    raise ValueError("Invalid preference for single route calculation")

                # Select the ith best mode, ensuring we provide different alternatives
                if i < len(sorted_modes):
                    best_mode = sorted_modes[i]
                else:
                    # If fewer modes are available, pick the last one
                    best_mode = sorted_modes[-1]

                # Append the selected mode for the segment to route_segments
                route_segments.append({
                    "from": from_node,
                    "to": to_node,
                    "distance": distance,
                    "selected_mode": best_mode
                })

            all_alternatives.append(route_segments)

        logging.debug(f"Generated {len(all_alternatives)} alternatives.")
        return all_alternatives
    except Exception as e:
        logging.error(f"Error in generate_single_route: {e}")
        raise

def calculate_balanced_route(route, distances, transport_modes):
    """
    Generate balanced routes using different weight combinations for time and cost.
    """
    try:
        logging.info(f"Generating balanced routes for route {route}.")
        weight_combinations = [
            (0.75, 0.25),  # Alternative 1: Strong emphasis on cost
            (0.80, 0.2),    # Alternative 2: Slight emphasis on cost
            (0.85, 0.15)    # Alternative 3: More emphasis on time
        ]

        all_alternatives = []

        for time_weight, cost_weight in weight_combinations:
            route_segments = []

            for i in range(len(route) - 1):
                from_node = route[i]
                to_node = route[i + 1]
                distance = distances[(from_node, to_node)]

                # Evaluate transport modes for the segment using TOPSIS
                mode_details = calculate_mode_details(from_node, to_node, distance, transport_modes)
                best_modes = topsis_evaluation(mode_details, time_weight, cost_weight)

                # Use the top-ranked mode
                best_mode = best_modes[0]

                route_segments.append({
                    "from": from_node,
                    "to": to_node,
                    "distance": distance,
                    "selected_mode": best_mode
                })

            all_alternatives.append(route_segments)

        # Ensure alternatives are distinct by adding some variation if they are identical
        seen_paths = set()
        final_alternatives = []
        for alternative in all_alternatives:
            path_signature = tuple(segment["selected_mode"]["mode"] for segment in alternative)
            if path_signature not in seen_paths:
                seen_paths.add(path_signature)
                final_alternatives.append(alternative)

        # If fewer than 3 distinct alternatives were found, fill up with available distinct options
        if len(final_alternatives) < 3:
            final_alternatives = all_alternatives[:3]

        logging.debug(f"Generated {len(final_alternatives)} balanced route alternatives.")
        return final_alternatives
    except Exception as e:
        logging.error(f"Error in calculate_balanced_route: {e}")
        raise

# Summary Functions

def summarize_alternatives(route_alternatives):
    """
    Summarize the route alternatives with total distance, cost, time, and path description.
    """
    try:
        logging.info(f"Summarizing {len(route_alternatives)} route alternatives.")
        summaries = []

        emoji_dict = {
            "Bus": "🚌",
            "Train": "🚂",
            "Walking": "🚶",
            "Bicycle": "🚴"
        }

        for alt_idx, route_segments in enumerate(route_alternatives):
            total_distance, total_cost, total_time = 0, 0, 0
            path_description = []

            for segment in route_segments:
                mode = segment["selected_mode"]["mode"]
                total_distance += segment["distance"]
                total_cost += segment["selected_mode"]["cost"]
                total_time += segment["selected_mode"]["total_time"]

                # Append current node and mode emoji to path description
                path_description.append(segment["from"])
                path_description.append(emoji_dict.get(mode, "🚘"))  # Default emoji for unknown mode

            # Append the last node (final destination)
            path_description.append(route_segments[-1]["to"])

            summaries.append({
                "Alternative": f"Alternative {alt_idx + 1}",
                "Total Distance (km)": total_distance,
                "Total Cost": total_cost,
                "Total Time (min)": total_time,
                "Path": " ".join(path_description)
            })

        logging.debug(f"Summarized {len(summaries)} alternatives.")
        return summaries
    except Exception as e:
        logging.error(f"Error in summarize_alternatives: {e}")
        raise

def display_alternatives(summaries, preference=None):
    """
    Display the route alternatives to the user with a summary of each.
    """
    try:
        logging.info("Displaying route alternatives to the user.")
        if preference in ["least_cost", "least_time"]:
            # Only display the single best alternative for least cost or least time
            summary = summaries[0]
            print("\n🌟 Route Alternative Summary 🌟")
            print(f"\n🔵 {summary['Alternative']}")
            print(f"  🚷 Total Distance: {summary['Total Distance (km)']:.2f} km")
            print(f"  💸 Total Cost: {summary['Total Cost']:.2f} units")
            print(f"  ⏳ Total Time: {summary['Total Time (min)']:.2f} minutes")
            print(f"  🛤 Path: {summary['Path']}")
        else:
            # Display all alternatives and let the user choose
            print("\n🌟 Route Alternatives Summary 🌟")
            for summary in summaries:
                print(f"\n🔵 {summary['Alternative']}")
                print(f"  🚷 Total Distance: {summary['Total Distance (km)']:.2f} km")
                print(f"  💸 Total Cost: {summary['Total Cost']:.2f} units")
                print(f"  ⏳ Total Time: {summary['Total Time (min)']:.2f} minutes")
                print(f"  🛤 Path: {summary['Path']}")

            while True:
                try:
                    selected_option = int(input("\n🔑 Select your preferred alternative (enter the number 1/2/3): ").strip())
                    if 1 <= selected_option <= len(summaries):
                        return selected_option - 1  # Return zero-indexed value
                    else:
                        print("❌ Invalid choice. Please enter a valid number.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number between 1 and 3.")
    except Exception as e:
        logging.error(f"Error in display_alternatives: {e}")
        raise

__all__ = [
    "calculate_route_preferences",
    "summarize_alternatives",
    "display_alternatives"
]