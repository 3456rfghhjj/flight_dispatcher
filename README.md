# Flight Dispatcher & FMC Companion

A dedicated flight simulation assistant designed for enthusiasts flying aircraft such as the Boeing 777F, Boeing 737, and Airbus series in modern flight simulators (e.g., Microsoft Flight Simulator 2024 / 2020 on PS5 and PC).

Running locally on macOS and Windows, it eliminates the need to switch away from your simulator to browse complex web dispatchers. Powered by Google's Gemini 3.8 Flash API, the tool plans authentic IFR routes, fetches radio navigation aids, converts fuel and cargo metrics, and computes weight and balance parameters on the fly.

---

## Features

- **Automated IFR Dispatch:** Generates realistic IFR airway routings, standard instrument departures (SID), standard terminal arrivals (STAR), flight levels, and estimated time en route (ETE) for any origin and destination pair worldwide.
- **Instrument Landing System (ILS) & NAV Radio:** Provides essential destination approach information at a glance, including primary ILS frequencies, inbound localizer course (CRS), station ident, and airfield elevation.
- **Metric to Imperial Conversion:** Live two-way tracking that converts tonnes directly into pounds (LBS) for fast and precise FMC/MCDU data entry.
- **Center of Gravity (% MAC) & Trim Calculations:** Calculates Zero Fuel Weight (ZFW), Takeoff Weight (TOW), Center of Gravity as a percentage of Mean Aerodynamic Chord (% MAC), and takeoff stabilizer trim values customized to the aircraft type.
- **Built-in Aircraft Profiles:**
  - Boeing 777F
  - Boeing 737-600
  - Cessna Citation X
  - Airbus A400M Atlas
  - Airbus A330-300
  - Airbus A320neo
- **High-Contrast Cockpit GUI:** Features an oversized, bold typography palette (16–24 pt) on a low-strain dark green background, optimized for readability from a distance on televisions and large displays.

---

## Prerequisites

- Python 3.9+
- Google GenAI SDK
- Active Gemini API Key (obtainable via Google AI Studio)

---

## Installation

1. Clone the repository:
   git clone https://github.com/your-username/flight-dispatcher-fmc.git
   cd flight-dispatcher-fmc

2. Install the required library:
   pip install google-genai

3. Configure your API Key:
   Open flight_dispatcher.py in your editor (e.g. Thonny) and replace the placeholder with your actual Gemini API key:
   GEMINI_API_KEY = "YOUR_ACTUAL_GEMINI_API_KEY"

---

## Running the Application

Launch the script directly from your terminal or IDE:

python flight_dispatcher.py

---

## Operating Instructions

1. **Enter Airfield Codes:** Input the 4-letter ICAO codes for ORIGIN and DEST (e.g., EDDM and KSFO).
2. **Select Aircraft:** Cycle through the available airframes using the ◀ and ▶ buttons.
3. **Dispatch:** Click DISPATCH FLIGHT to request routing and arrival data via the Gemini 3.8 Flash API.
4. **Input Weights:** Enter your planned fuel and payload in tonnes. Total weights, % MAC, and Stab Trim will compute automatically for your FMC Takeoff Reference page.
