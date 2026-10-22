import tkinter as tk
from tkinter import messagebox
import json
from google import genai
from google.genai import types

# --- INSERT YOUR GEMINI API KEY HERE ---
GEMINI_API_KEY = "your_API_key_here"

KG_TO_LBS = 2.20462262

# Aircraft performance profiles for Weight, CG (% MAC) and Trim calculations
AIRCRAFT_DATA = {
    "Boeing 777F": {
        "oew_t": 144.5, "base_cg": 24.5, "cg_cgo_k": 0.037, "cg_fuel_k": 0.010,
        "trim_base": 8.1, "trim_k": 0.16, "flaps": "Flaps 15"
    },
    "Boeing 737-600": {
        "oew_t": 36.4, "base_cg": 20.0, "cg_cgo_k": 0.080, "cg_fuel_k": 0.025,
        "trim_base": 7.5, "trim_k": 0.14, "flaps": "Flaps 5"
    },
    "Cessna Citation X": {
        "oew_t": 9.8, "base_cg": 22.0, "cg_cgo_k": 0.150, "cg_fuel_k": 0.040,
        "trim_base": 6.2, "trim_k": 0.12, "flaps": "Flaps 15"
    },
    "Airbus A400M": {
        "oew_t": 76.5, "base_cg": 26.0, "cg_cgo_k": 0.050, "cg_fuel_k": 0.015,
        "trim_base": 5.0, "trim_k": 0.10, "flaps": "Flaps 2"
    },
    "Airbus A330-300": {
        "oew_t": 124.5, "base_cg": 25.0, "cg_cgo_k": 0.040, "cg_fuel_k": 0.012,
        "trim_base": 4.5, "trim_k": 0.09, "flaps": "1+F"
    },
    "Airbus A320neo": {
        "oew_t": 44.3, "base_cg": 25.0, "cg_cgo_k": 0.070, "cg_fuel_k": 0.020,
        "trim_base": 4.0, "trim_k": 0.08, "flaps": "Flaps 1"
    }
}

aircraft_list = list(AIRCRAFT_DATA.keys())
aircraft_index = 0

def recalculate_weights(*args):
    ac_name = aircraft_list[aircraft_index]
    ac = AIRCRAFT_DATA[ac_name]

    try:
        fuel_str = ent_fuel.get().replace(",", ".").strip()
        cgo_str = ent_cargo.get().replace(",", ".").strip()

        fuel_t = float(fuel_str) if fuel_str else 0.0
        cgo_t = float(cgo_str) if cgo_str else 0.0

        fuel_lbs = fuel_t * 1000.0 * KG_TO_LBS
        cgo_lbs = cgo_t * 1000.0 * KG_TO_LBS

        val_fuel_lbs.config(text=f"{fuel_lbs:,.0f} lbs   [{fuel_lbs/1000:.1f}k]")
        val_cargo_lbs.config(text=f"{cgo_lbs:,.0f} lbs   [{cgo_lbs/1000:.1f}k]")

        oew_t = ac["oew_t"]
        zfw_t = oew_t + cgo_t
        zfw_lbs = zfw_t * 1000.0 * KG_TO_LBS

        tow_t = zfw_t + fuel_t
        tow_lbs = tow_t * 1000.0 * KG_TO_LBS

        val_zfw.config(text=f"{zfw_t:.1f} t   |   {zfw_lbs:,.0f} lbs")
        val_tow.config(text=f"{tow_t:.1f} t   |   {tow_lbs:,.0f} lbs")

        zfw_cg = ac["base_cg"] + (cgo_t * ac["cg_cgo_k"])
        tow_cg = zfw_cg + (fuel_t * ac["cg_fuel_k"])

        stab_trim = ac["trim_base"] - (ac["trim_k"] * tow_cg)
        stab_trim = max(1.5, min(9.0, stab_trim))

        val_zfw_cg.config(text=f"{zfw_cg:.1f} % MAC")
        val_tow_cg.config(text=f"{tow_cg:.1f} % MAC")
        lbl_trim_title.config(text=f"STAB TRIM ({ac['flaps']}):")
        val_trim.config(text=f"{stab_trim:.2f} UP")
    except ValueError:
        pass

def next_aircraft(event=None):
    global aircraft_index
    aircraft_index = (aircraft_index + 1) % len(aircraft_list)
    update_aircraft_display()

def prev_aircraft(event=None):
    global aircraft_index
    aircraft_index = (aircraft_index - 1) % len(aircraft_list)
    update_aircraft_display()

def update_aircraft_display():
    name = aircraft_list[aircraft_index]
    lbl_ac_name.config(text=name)
    recalculate_weights()

def generate_flight_plan():
    dep = ent_dep.get().strip().upper()
    arr = ent_arr.get().strip().upper()
    aircraft = aircraft_list[aircraft_index]

    if not dep or not arr:
        messagebox.showwarning("Input Required", "Please enter both Origin and Destination ICAO codes (e.g. EDDF and KJFK)!")
        return

    if GEMINI_API_KEY in ["your_API-here", "SEM_VLOZTE_VAS_GEMINI_API_KLUC"]:
        messagebox.showerror("API Key Missing", "Please configure your Gemini API key in the GEMINI_API_KEY variable!")
        return

    lbl_info_flight.config(text=f"Gemini API is generating flight plan for {dep} -> {arr}...", fg=GREEN_PASTEL)
    root.update_idletasks()

    prompt = f"""
    You are an expert aviation flight dispatcher for IFR flight simulators (MSFS / Navigraph AIRAC database).
    Generate a realistic, optimal flight plan from {dep} to {arr} for a {aircraft}.

    Return ONLY a raw JSON object without markdown formatting, following this exact schema:
    {{
        "distance_nm": 420,
        "cruise_alt": "FL340",
        "flight_time": "1h 05m",
        "sid": "departure SID procedure and expected runway",
        "star": "arrival STAR procedure and expected runway",
        "route": "full IFR airway routing string",
        "legs": "clean sequence of waypoints separated by -> for FMC LEGS",
        "ils_freq": "arrival runway ILS frequency in MHz",
        "ils_crs": "inbound localizer course in degrees",
        "ils_ident": "ILS station identifier",
        "elev": "destination airfield elevation in ft"
    }}
    """

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        chat = client.chats.create(
            model="gemini-3.8-flash",
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        response = chat.send_message(prompt)

        data = json.loads(response.text)

        lbl_info_flight.config(
            text=f"Distance: {data.get('distance_nm', '---')} NM   |   Cruise: {data.get('cruise_alt', '---')}   |   ETE: {data.get('flight_time', '---')}   (Gemini 3.8 Flash)",
            fg=AMBER_WARN
        )

        ent_sid.delete(0, tk.END)
        ent_sid.insert(0, data.get("sid", "---"))

        ent_star.delete(0, tk.END)
        ent_star.insert(0, data.get("star", "---"))

        txt_route.delete("1.0", tk.END)
        txt_route.insert(tk.END, data.get("route", "---"))

        txt_legs.delete("1.0", tk.END)
        txt_legs.insert(tk.END, data.get("legs", "---"))

        val_ils_freq.config(text=data.get("ils_freq", "---"))
        val_ils_crs.config(text=data.get("ils_crs", "---"))
        val_ils_ident.config(text=data.get("ils_ident", "---"))
        val_ils_elev.config(text=data.get("elev", "---"))

    except Exception as e:
        messagebox.showerror("API Error", f"Failed to generate flight plan:\n{str(e)}")
        lbl_info_flight.config(text="API connection failed.", fg="red")

# --- GUI SETUP ---
root = tk.Tk()
root.title("Flight Dispatcher & FMC Companion (Gemini 3.8 Flash)")
root.geometry("1400x1000")
root.resizable(True, True)

try:
    root.attributes("-zoomed", True)
except Exception:
    pass

BG_DARK      = "#131a15"
CARD_BG      = "#1c2620"
TEXT_MAIN    = "#dbe6de"
GREEN_PASTEL = "#8fd19e"
GREEN_ACCENT = "#5cb874"
AMBER_WARN   = "#e5b567"
ENTRY_BG     = "#0b100d"
PANEL_SEL    = "#163124"

root.configure(bg=BG_DARK)

main_box = tk.Frame(root, bg=BG_DARK)
main_box.pack(fill="both", expand=True, padx=20, pady=10)

# 1. TOP PANEL: FLIGHT ROUTE & PROCEDURES
frame_top = tk.LabelFrame(main_box, text=" 1. FLIGHT PLAN, PROCEDURES & ROUTING (GEMINI 3.8 DISPATCH) ",
                          bg=CARD_BG, fg=GREEN_PASTEL, font=("Helvetica", 16, "bold"), padx=18, pady=10)
frame_top.pack(fill="both", expand=True, pady=6)

f_in = tk.Frame(frame_top, bg=CARD_BG)
f_in.pack(fill="x", pady=4)

tk.Label(f_in, text="ORIGIN:", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 16, "bold")).pack(side="left", padx=4)
ent_dep = tk.Entry(f_in, width=6, bg=ENTRY_BG, fg=GREEN_PASTEL, insertbackground=GREEN_PASTEL,
                   font=("Courier", 20, "bold"), relief="flat", justify="center")
ent_dep.pack(side="left", padx=6)
ent_dep.focus()

tk.Label(f_in, text="DEST:", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 16, "bold")).pack(side="left", padx=(12, 4))
ent_arr = tk.Entry(f_in, width=6, bg=ENTRY_BG, fg=GREEN_PASTEL, insertbackground=GREEN_PASTEL,
                   font=("Courier", 20, "bold"), relief="flat", justify="center")
ent_arr.pack(side="left", padx=6)

tk.Label(f_in, text="Aircraft:", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 16, "bold")).pack(side="left", padx=(20, 6))

f_ac_selector = tk.Frame(f_in, bg=PANEL_SEL, relief="solid", bd=1)
f_ac_selector.pack(side="left", padx=6)

btn_prev = tk.Label(f_ac_selector, text=" ◀ ", bg=PANEL_SEL, fg=GREEN_PASTEL, font=("Helvetica", 16, "bold"), cursor="hand2")
btn_prev.pack(side="left", padx=6, pady=4)
btn_prev.bind("<Button-1>", prev_aircraft)

lbl_ac_name = tk.Label(f_ac_selector, text="Boeing 777F", bg=PANEL_SEL, fg="#ffffff", font=("Helvetica", 16, "bold"), width=18)
lbl_ac_name.pack(side="left", padx=10, pady=4)
lbl_ac_name.bind("<Button-1>", next_aircraft)

btn_next = tk.Label(f_ac_selector, text=" ▶ ", bg=PANEL_SEL, fg=GREEN_PASTEL, font=("Helvetica", 16, "bold"), cursor="hand2")
btn_next.pack(side="left", padx=6, pady=4)
btn_next.bind("<Button-1>", next_aircraft)

btn_calc = tk.Button(f_in, text="  DISPATCH FLIGHT  ", command=generate_flight_plan,
                     bg=GREEN_ACCENT, fg="#08140c", font=("Helvetica", 15, "bold"), relief="flat", cursor="hand2", padx=16, pady=4)
btn_calc.pack(side="right", padx=10)

lbl_info_flight = tk.Label(frame_top, text="Enter ICAO codes (e.g. EDDM -> KSFO) and click 'DISPATCH FLIGHT'.",
                           bg=CARD_BG, fg=AMBER_WARN, font=("Helvetica", 15, "bold"))
lbl_info_flight.pack(anchor="w", pady=4)

f_proc = tk.Frame(frame_top, bg=CARD_BG)
f_proc.pack(fill="x", pady=4)

tk.Label(f_proc, text="DEPARTURE SID:", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 14, "bold")).grid(row=0, column=0, sticky="w")
ent_sid = tk.Entry(f_proc, width=32, bg=ENTRY_BG, fg=AMBER_WARN, font=("Helvetica", 14, "bold"), relief="flat")
ent_sid.grid(row=0, column=1, padx=10, sticky="w")

tk.Label(f_proc, text="ARRIVAL STAR:", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 14, "bold")).grid(row=0, column=2, padx=(20, 0), sticky="w")
ent_star = tk.Entry(f_proc, width=32, bg=ENTRY_BG, fg=AMBER_WARN, font=("Helvetica", 14, "bold"), relief="flat")
ent_star.grid(row=0, column=3, padx=10, sticky="w")

tk.Label(frame_top, text="Full IFR Airway Routing (FMC ROUTE):", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 13)).pack(anchor="w", pady=(4,0))
txt_route = tk.Text(frame_top, height=2, bg=ENTRY_BG, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
                    font=("Courier", 16), relief="flat", padx=10, pady=6)
txt_route.pack(fill="x", pady=2)

tk.Label(frame_top, text="Waypoint Sequence (FMC LEGS):", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 13, "bold")).pack(anchor="w", pady=(4,0))
txt_legs = tk.Text(frame_top, height=3, bg=ENTRY_BG, fg=GREEN_PASTEL, insertbackground=GREEN_PASTEL,
                   font=("Courier", 18, "bold"), relief="flat", padx=10, pady=6)
txt_legs.pack(fill="both", expand=True, pady=2)

# 2. PANEL: ARRIVAL RUNWAY & ILS RADIO
frame_ils = tk.LabelFrame(main_box, text=" 2. DESTINATION RUNWAY & ILS RADIO (FMC NAV RAD) ",
                          bg=CARD_BG, fg=GREEN_PASTEL, font=("Helvetica", 16, "bold"), padx=18, pady=10)
frame_ils.pack(fill="both", expand=True, pady=6)

f_ils_cards = tk.Frame(frame_ils, bg=CARD_BG)
f_ils_cards.pack(fill="both", expand=True)

b_ils1 = tk.Frame(f_ils_cards, bg=ENTRY_BG, padx=10, pady=8)
b_ils1.pack(side="left", expand=True, fill="both", padx=6)
tk.Label(b_ils1, text="ILS Frequency (NAV1):", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).pack()
val_ils_freq = tk.Label(b_ils1, text="---", bg=ENTRY_BG, fg=GREEN_PASTEL, font=("Courier", 24, "bold"))
val_ils_freq.pack(pady=4)

b_ils2 = tk.Frame(f_ils_cards, bg=ENTRY_BG, padx=10, pady=8)
b_ils2.pack(side="left", expand=True, fill="both", padx=6)
tk.Label(b_ils2, text="Inbound Course (CRS):", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).pack()
val_ils_crs = tk.Label(b_ils2, text="---", bg=ENTRY_BG, fg=GREEN_PASTEL, font=("Courier", 24, "bold"))
val_ils_crs.pack(pady=4)

b_ils3 = tk.Frame(f_ils_cards, bg=ENTRY_BG, padx=10, pady=8)
b_ils3.pack(side="left", expand=True, fill="both", padx=6)
tk.Label(b_ils3, text="Identifier / Runway:", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).pack()
val_ils_ident = tk.Label(b_ils3, text="---", bg=ENTRY_BG, fg=AMBER_WARN, font=("Helvetica", 20, "bold"))
val_ils_ident.pack(pady=6)

b_ils4 = tk.Frame(f_ils_cards, bg=ENTRY_BG, padx=10, pady=8)
b_ils4.pack(side="left", expand=True, fill="both", padx=6)
tk.Label(b_ils4, text="Field Elevation:", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).pack()
val_ils_elev = tk.Label(b_ils4, text="---", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 20, "bold"))
val_ils_elev.pack(pady=6)

# 3. PANEL: WEIGHT & FUEL CONVERSION
frame_mid = tk.LabelFrame(main_box, text=" 3. WEIGHT & FUEL MANAGEMENT (TONNES -> POUNDS) ",
                          bg=CARD_BG, fg=GREEN_PASTEL, font=("Helvetica", 16, "bold"), padx=18, pady=10)
frame_mid.pack(fill="both", expand=True, pady=6)

f_weights = tk.Frame(frame_mid, bg=CARD_BG)
f_weights.pack(fill="x")

tk.Label(f_weights, text="Fuel (Tonnes):", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 15, "bold")).grid(row=0, column=0, sticky="w", pady=4)
ent_fuel = tk.Entry(f_weights, width=9, bg=ENTRY_BG, fg=GREEN_PASTEL, insertbackground=GREEN_PASTEL,
                    font=("Helvetica", 18, "bold"), relief="flat", justify="center")
ent_fuel.grid(row=0, column=1, padx=10, pady=4)
ent_fuel.insert(0, "45.0")
ent_fuel.bind("<KeyRelease>", recalculate_weights)

tk.Label(f_weights, text="-> In Pounds (FMC LBS):", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 15)).grid(row=0, column=2, sticky="w", padx=16)
val_fuel_lbs = tk.Label(f_weights, text="---", bg=CARD_BG, fg=GREEN_PASTEL, font=("Courier", 20, "bold"))
val_fuel_lbs.grid(row=0, column=3, sticky="w")

tk.Label(f_weights, text="Payload / Cargo (Tonnes):", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 15, "bold")).grid(row=1, column=0, sticky="w", pady=4)
ent_cargo = tk.Entry(f_weights, width=9, bg=ENTRY_BG, fg=GREEN_PASTEL, insertbackground=GREEN_PASTEL,
                     font=("Helvetica", 18, "bold"), relief="flat", justify="center")
ent_cargo.grid(row=1, column=1, padx=10, pady=4)
ent_cargo.insert(0, "55.0")
ent_cargo.bind("<KeyRelease>", recalculate_weights)

tk.Label(f_weights, text="-> In Pounds (FMC LBS):", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 15)).grid(row=1, column=2, sticky="w", padx=16)
val_cargo_lbs = tk.Label(f_weights, text="---", bg=CARD_BG, fg=GREEN_PASTEL, font=("Courier", 20, "bold"))
val_cargo_lbs.grid(row=1, column=3, sticky="w")

f_totals = tk.Frame(frame_mid, bg=CARD_BG)
f_totals.pack(fill="x", pady=4)

tk.Label(f_totals, text="Planned ZFW:", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).grid(row=0, column=0, sticky="w")
val_zfw = tk.Label(f_totals, text="---", bg=CARD_BG, fg=TEXT_MAIN, font=("Courier", 17, "bold"))
val_zfw.grid(row=0, column=1, sticky="w", padx=12)

tk.Label(f_totals, text="Planned TOW:", bg=CARD_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).grid(row=0, column=2, sticky="w", padx=(30, 0))
val_tow = tk.Label(f_totals, text="---", bg=CARD_BG, fg=TEXT_MAIN, font=("Courier", 17, "bold"))
val_tow.grid(row=0, column=3, sticky="w", padx=12)

# 4. PANEL: AIRCRAFT BALANCE & STAB TRIM
frame_cg = tk.LabelFrame(main_box, text=" 4. BALANCING & TRIM (PERF INIT & TAKEOFF) ",
                         bg=CARD_BG, fg=GREEN_PASTEL, font=("Helvetica", 16, "bold"), padx=18, pady=10)
frame_cg.pack(fill="both", expand=True, pady=6)

f_cg_cards = tk.Frame(frame_cg, bg=CARD_BG)
f_cg_cards.pack(fill="both", expand=True)

b1 = tk.Frame(f_cg_cards, bg=ENTRY_BG, padx=10, pady=8)
b1.pack(side="left", expand=True, fill="both", padx=6)
tk.Label(b1, text="ZFW CG (FMC PERF):", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).pack()
val_zfw_cg = tk.Label(b1, text="---", bg=ENTRY_BG, fg=AMBER_WARN, font=("Helvetica", 24, "bold"))
val_zfw_cg.pack(pady=4)

b2 = tk.Frame(f_cg_cards, bg=ENTRY_BG, padx=10, pady=8)
b2.pack(side="left", expand=True, fill="both", padx=6)
tk.Label(b2, text="TOW CG (Takeoff):", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 14)).pack()
val_tow_cg = tk.Label(b2, text="---", bg=ENTRY_BG, fg=AMBER_WARN, font=("Helvetica", 24, "bold"))
val_tow_cg.pack(pady=4)

b3 = tk.Frame(f_cg_cards, bg=ENTRY_BG, padx=10, pady=8)
b3.pack(side="left", expand=True, fill="both", padx=6)
lbl_trim_title = tk.Label(b3, text="STAB TRIM:", bg=ENTRY_BG, fg=TEXT_MAIN, font=("Helvetica", 14))
lbl_trim_title.pack()
val_trim = tk.Label(b3, text="---", bg=ENTRY_BG, fg=GREEN_PASTEL, font=("Helvetica", 24, "bold"))
val_trim.pack(pady=4)

recalculate_weights()

root.mainloop()