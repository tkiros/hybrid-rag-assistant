"""Hand-written vocabulary for the synthetic corpus. data/generate.py turns it into two PDFs.

Everything here is fictional: Halvard Machine Works and its RS-Series compressors don't exist.
Text is Latin-1 only, because the PDFs use fpdf2's built-in core fonts.
"""

MODELS = ["RS-30", "RS-45", "RS-55", "RS-75", "RS-90"]

# One chapter per category, in manual order: (chapter title, part-number prefix).
CATEGORIES = {
    "air_end": ("AIR END", "HX"),
    "lubrication": ("LUBRICATION SYSTEM", "LB"),
    "cooling": ("COOLING SYSTEM", "CL"),
    "drive": ("DRIVE SYSTEM", "DR"),
    "filtration": ("FILTRATION", "FT"),
    "electrical": ("ELECTRICAL AND CONTROLS", "EL"),
    "pressure": ("PRESSURE SYSTEM", "PV"),
}

# (category, name used in the manual, a different name a user might use, fastener, what it does).
# The alternative name shares as few words as possible with the manual's name: that is what
# makes the "paraphrased" questions hard for keyword search.
COMPONENTS = [
    ("air_end", "air end assembly", "screw compression element", "M16 mounting bolts",
     "compresses the intake air between two meshing helical rotors"),
    ("air_end", "inlet valve", "intake throttle", "M10 flange bolts",
     "opens to load the compressor and closes to unload it"),
    ("air_end", "minimum pressure valve", "pressure-maintaining valve", "M12 body bolts",
     "holds back delivery until the separator tank has built up enough pressure"),
    ("air_end", "discharge check valve", "outlet non-return valve", "M10 union nuts",
     "stops compressed air flowing back into the air end at shutdown"),
    ("air_end", "rotor shaft seal", "spindle lip seal", "M6 retainer screws",
     "keeps oil from escaping where the male rotor shaft leaves the housing"),
    ("air_end", "bearing housing cover", "end cap over the rotor bearings", "M8 cover screws",
     "closes the bearing chamber at the discharge end of the air end"),
    ("lubrication", "oil separator cartridge", "coalescer element", "M8 cover bolts",
     "strips oil mist out of the compressed air inside the separator tank"),
    ("lubrication", "oil filter", "lube canister", "spin-on thread",
     "removes particles from the oil before it reaches the bearings"),
    ("lubrication", "thermostatic mixing valve", "lubricant thermostat", "M8 housing screws",
     "sends oil through the cooler only when it is warm enough"),
    ("lubrication", "oil level sight glass", "lubricant gauge window", "threaded bezel",
     "shows the oil level in the separator tank"),
    ("lubrication", "oil drain valve", "sump tap", "1/2 inch BSP thread",
     "lets the oil be drained from the bottom of the separator tank"),
    ("lubrication", "scavenge line", "return tube from the coalescer", "JIC swivel nuts",
     "returns oil collected in the separator element to the air end"),
    ("cooling", "aftercooler core", "compressed-air radiator", "M8 frame bolts",
     "cools the compressed air before it leaves the machine"),
    ("cooling", "oil cooler core", "lubricant radiator", "M8 frame screws",
     "removes heat from the oil returning to the air end"),
    ("cooling", "cooling fan motor", "blower drive for the radiators", "M10 bracket bolts",
     "drives the fan that pulls ambient air across both coolers"),
    ("cooling", "fan shroud", "fan cowling", "M6 panel screws",
     "directs the fan airflow across the cooler cores"),
    ("cooling", "condensate drain valve", "automatic water trap", "3/8 inch BSP thread",
     "discharges water that condenses out of the cooled air"),
    ("cooling", "moisture separator", "droplet trap after the cooler", "M10 flange bolts",
     "removes liquid water droplets from the air leaving the aftercooler"),
    ("drive", "drive coupling", "flexible motor-to-compressor joint", "M12 hub bolts",
     "transmits torque from the main motor to the air end"),
    ("drive", "drive belt set", "V-belts", "M12 motor slide bolts",
     "transmits power from the motor pulley on belt-driven models"),
    ("drive", "belt tensioner", "tensioning arm", "M10 pivot bolt",
     "keeps the drive belts at the correct tension"),
    ("drive", "main motor", "primary electric drive", "M20 foot bolts",
     "is the electric motor that drives the air end"),
    ("drive", "drive-end motor bearing", "front bearing of the electric drive", "M8 cap screws",
     "supports the motor shaft at the coupling end"),
    ("drive", "anti-vibration mounts", "rubber isolation feet", "M12 stud nuts",
     "isolate the motor and air end from the frame"),
    ("filtration", "air intake filter element", "suction air cleaner", "wing nut",
     "cleans the air before it enters the inlet valve"),
    ("filtration", "pre-filter mat", "cabinet ventilation foam pad", "M5 frame screws",
     "keeps dust out of the cabinet cooling air"),
    ("filtration", "coalescing line filter", "downstream oil-removal cartridge", "bowl thread",
     "removes residual oil aerosol from the delivered air"),
    ("filtration", "filter restriction indicator", "clog warning gauge", "push-in fitting",
     "signals when the intake filter element needs changing"),
    ("electrical", "main contactor", "motor starter switch", "M5 terminal screws",
     "connects the main motor to the supply"),
    ("electrical", "star-delta timer", "Y-D changeover relay", "M4 terminal screws",
     "sets the delay before the motor switches from star to delta"),
    ("electrical", "pressure transducer", "outlet pressure sender", "1/4 inch BSP thread",
     "measures delivery pressure for the controller"),
    ("electrical", "temperature probe", "discharge heat sensor", "M14 sensor thread",
     "measures the air end discharge temperature"),
    ("electrical", "controller display module", "front-panel screen", "M4 bezel screws",
     "shows operating data and alarms"),
    ("electrical", "emergency stop button", "red kill switch", "M22 locking ring",
     "stops the machine immediately when pressed"),
    ("electrical", "control transformer", "step-down unit for the control circuit",
     "M6 mounting screws", "supplies 24 volts to the control circuit"),
    ("electrical", "phase monitor relay", "phase-loss protector", "M4 terminal screws",
     "trips the machine if a supply phase is missing or reversed"),
    ("pressure", "load solenoid valve", "electric loading actuator", "M5 coil nut",
     "switches control air to open or close the inlet valve"),
    ("pressure", "safety relief valve", "pressure pop-off", "3/4 inch BSP thread",
     "opens if the separator tank pressure exceeds its set point"),
    ("pressure", "separator tank", "air-oil receiver vessel", "M20 foot bolts",
     "holds the oil reservoir and separates oil from the compressed air"),
    ("pressure", "blowdown valve", "shutdown venting valve", "M8 body screws",
     "vents the separator tank pressure when the machine stops"),
]

# Extra catalog-only parts, named "<KIND>, <COMPONENT>" (e.g. "GASKET, INLET VALVE").
EXTRA_PART_KINDS = {
    "default": ["GASKET", "SEAL KIT", "REPAIR KIT", "MOUNTING BRACKET", "BOLT SET", "O-RING SET"],
    "electrical": ["TERMINAL COVER", "MOUNTING BRACKET", "CABLE GLAND KIT", "FUSE SET",
                   "CONNECTOR PLUG", "LABEL SET"],
}

PANELS = ["front service panel", "left-hand side panel", "right-hand side panel", "top cover",
          "rear louvre panel"]
CONNECTIONS = ["oil lines", "air hoses", "wiring loom connector", "control air tube",
               "sensor cable"]

# Procedure sentences. {c} = component, {panel}, {conn}, {n} = minutes, {mm} = wear limit.
REMOVAL_STEPS = [
    "Stop the compressor, open the main isolator and fit a padlock and warning tag.",
    "Vent all residual pressure and confirm the gauge reads zero before loosening any fitting "
    "on the {c}.",
    "Allow the machine to cool for at least {n} minutes; surfaces near the {c} can be hot "
    "enough to burn.",
    "Remove the {panel} to gain access to the {c}.",
    "Mark the orientation of the {c} with a paint pen so it can be refitted the same way.",
    "Disconnect the {conn} and cap the open ports to keep dirt out.",
    "Support the {c} while removing the last fastener; never let it hang on hoses or cables.",
    "Place the removed {c} on a clean bench and keep its fasteners in a labelled tray.",
]
INSTALL_STEPS = [
    "Clean the mating faces and fit a new gasket or O-ring; never reuse an old seal.",
    "Lightly lubricate new O-rings with clean compressor oil before assembly.",
    "Offer the {c} into position using the orientation mark made during removal.",
    "Fit all fasteners finger-tight first, then tighten them evenly in a cross pattern.",
    "Reconnect the {conn} and check that nothing can rub against moving parts.",
    "Refit the {panel}, restore power and run the machine unloaded for {n} minutes while "
    "checking for leaks around the {c}.",
]
TORQUE_SENTENCE = "Tighten the {fastener} of the {c} to {torque} Nm."
INSPECTION_STEPS = [
    "Inspect the {c} for cracks, corrosion and signs of overheating such as scorched paint.",
    "Replace the {c} if wear exceeds {mm} mm at any measured point.",
    "A wet or oily surface on the {c} usually points to a failing seal.",
    "Check that all fasteners on the {c} are present and that locking compound is intact.",
    "Record the inspection result and the operating hours in the maintenance log.",
    "Compare the condition of the {c} with the photographs in the service bulletin before "
    "deciding to reuse it.",
]
TROUBLESHOOTING_STEPS = [
    "If the {c} leaks after assembly, check the seal seating and the fastener torque before "
    "replacing parts.",
    "A rattling {c} usually means a loose fastener or a worn bearing surface.",
    "If the controller reports a fault on the {c} straight after a service, check the connector "
    "and the orientation mark.",
    "A {c} that runs hot often has a blocked cooling path; clean the surrounding area first.",
    "Vibration around the {c} can come from a loose mounting; recheck all fasteners.",
    "If the same fault returns within a few weeks, replace the {c} as a complete unit.",
    "Persistent oil mist near the {c} points to a failing seal.",
]
DESCRIPTION_EXTRA = [
    "The {c} is fitted to every RS-Series model; dimensions differ between frame sizes.",
    "Use only genuine Halvard parts when servicing the {c}.",
    "Most faults reported on the {c} are caused by dirty oil or incorrect assembly.",
    "The {c} can be serviced without removing the air end from the frame.",
]

# Error codes: (title suffix, when it triggers). {c} = component, {n} = a number.
SYMPTOMS = [
    ("FAILED TO OPEN", "the {c} does not open within {n} seconds of a load request"),
    ("FAILED TO CLOSE", "the {c} is still open {n} seconds after an unload request"),
    ("OVERTEMPERATURE", "the temperature at the {c} stays above {n} degrees C for 10 seconds"),
    ("SIGNAL LOST", "no valid signal is received from the {c} for {n} seconds"),
    ("PRESSURE DROP HIGH", "the pressure drop across the {c} exceeds 0.{n} bar"),
    ("LEAK DETECTED", "pressure decays by more than {n} percent within a minute of unloading "
                      "near the {c}"),
    ("WEAR LIMIT REACHED", "the operating hours logged for the {c} pass its wear limit by "
                           "{n} hours"),
    ("OVERLOAD", "the current drawn through the {c} exceeds its rating by {n} percent"),
]
CAUSES = [
    "worn or damaged internal parts",
    "contamination from dirty oil or air",
    "a loose connector or broken wire",
    "incorrect assembly after the last service",
    "operation outside the permitted ambient temperature",
    "a blocked or kinked control line",
]
RESETS = [
    "press RESET once the cause has been cleared",
    "hold STOP for five seconds, then press RESET",
    "switch the main isolator off for one minute and back on",
    "acknowledge the alarm on the display and restart the machine",
]

# Static chapters of the manual: {chapter title: [(section title, [paragraphs])]}.
MANUAL_INTRO = {
    "INTRODUCTION": [
        ("ABOUT THIS MANUAL", [
            "This manual covers installation, operation, service and spare parts for Halvard "
            "RS-Series oil-injected rotary screw compressors. Read the safety chapter before "
            "carrying out any work on the machine.",
            "Procedures are grouped by system. Each component section describes what the part "
            "does, how to remove and install it, and how to inspect it. Part numbers, prices and "
            "replacement intervals are listed in the parts catalog at the end of this manual.",
        ]),
        ("HOW TO USE THE PARTS CATALOG", [
            "Every catalog entry lists the part number, the models it fits, the unit price, the "
            "warranty class and the replacement interval in operating hours. Warranty classes "
            "are explained in the Halvard returns and warranty policy handbook.",
            "Always quote the full part number, including the final letter, when ordering. The "
            "final letter identifies the revision; earlier revisions may not fit.",
        ]),
    ],
    "SAFETY": [
        ("GENERAL SAFETY RULES", [
            "Only trained and authorised personnel may operate or service the compressor. Keep "
            "this manual with the machine and make sure every operator has read it.",
            "Never modify the compressor or bypass a safety device. Modifications void the "
            "warranty and may cause serious injury.",
        ]),
        ("LOCKOUT AND TAGOUT", [
            "Before any service work, stop the machine, open the main isolator and lock it in "
            "the off position. Attach a warning tag with your name and the date.",
            "An automatic restart can occur after a power failure if remote start is enabled. "
            "Disable remote start before opening any panel.",
        ]),
        ("STORED PRESSURE", [
            "The separator tank holds compressed air and hot oil. Vent the system completely and "
            "check the pressure gauge before loosening any pressurised fitting.",
            "Never use compressed air to clean clothing or skin.",
        ]),
        ("HOT SURFACES", [
            "The air end, discharge pipe and oil cooler reach high temperatures during "
            "operation. Allow the machine to cool before touching internal parts.",
        ]),
        ("ELECTRICAL HAZARDS", [
            "Lethal voltages are present in the starter cabinet. Capacitors in variable-speed "
            "drives can hold a charge after isolation; wait for the discharge time shown on the "
            "drive label.",
        ]),
        ("LIFTING AND TRANSPORT", [
            "Lift the compressor only by the forklift pockets or the marked lifting points. Never "
            "lift by the motor, the cooler or the piping.",
        ]),
    ],
    "INSTALLATION": [
        ("SITE REQUIREMENTS", [
            "Install the compressor indoors on a level, non-combustible floor in a clean, dry and "
            "well-ventilated room. Ambient temperature must stay between 2 and 46 degrees C.",
            "Leave at least one metre of free space around the machine for service access and "
            "cooling airflow.",
        ]),
        ("VENTILATION", [
            "Hot cooling air must be ducted out of the compressor room or extracted by a fan. "
            "Recirculated hot air raises the discharge temperature and causes shutdowns.",
        ]),
        ("PIPING CONNECTIONS", [
            "Connect the air outlet with a flexible hose or a pipe that does not load the "
            "compressor outlet. Fit an isolating valve between the compressor and the air "
            "network.",
            "Route condensate drain lines to an approved oil-water separator. Never discharge "
            "condensate directly into a drain.",
        ]),
        ("ELECTRICAL CONNECTION", [
            "The supply cable, fuses and isolator must be sized to local regulations for the "
            "motor rating on the data plate. Check the phase sequence before the first start.",
        ]),
    ],
    "OPERATION": [
        ("FIRST START", [
            "Check the oil level, close all panels and confirm that the outlet valve is open. "
            "Press START; the machine runs unloaded, then loads automatically once the star-delta "
            "changeover is complete.",
        ]),
        ("NORMAL STOP", [
            "Press STOP. The compressor unloads, runs on for a short period to vent the separator "
            "tank, and then stops. Do not open the isolator while the run-on period is active.",
        ]),
        ("CONTROL MODES", [
            "In automatic mode the controller stops the motor after a set unloaded period and "
            "restarts it when pressure falls. In continuous mode the motor keeps running "
            "unloaded.",
        ]),
        ("COLD WEATHER OPERATION", [
            "Below 2 degrees C, condensate can freeze in drain lines and the controller blocks "
            "the start. Heat the room or fit the optional cabinet heater.",
        ]),
    ],
}

MAINTENANCE_SCHEDULE = [
    ("DAILY CHECKS", [
        "Check the oil level in the sight glass while the machine is stopped. Check the display "
        "for warnings and confirm that condensate is being discharged.",
    ]),
    ("WEEKLY CHECKS", [
        "Inspect the intake filter restriction indicator and the cabinet pre-filter mat. Look "
        "for oil leaks under the machine.",
    ]),
    ("SERVICE VISITS", [
        "A certified technician must carry out scheduled service visits. Replacement intervals "
        "for individual parts are listed in the parts catalog.",
    ]),
]

# Model specifications: one block per model, generated from these ranges.
SPEC_LINE = ("Model {model}: rated pressure {bar} bar, free air delivery {fad} cubic metres per "
             "minute, motor power {kw} kW, oil capacity {oil} litres, weight {kg} kg.")


# ---------------------------------------------------------------- policy handbook
# Policy facts: (chapter, section, clause title, sentence with {v}, value kind, paraphrase).
# The paraphrase is how a customer would ask without knowing the clause number.
POLICY_FACTS = [
    ("ORDERS AND CANCELLATIONS", "STANDARD ORDERS", "ORDER CONFIRMATION",
     "Halvard confirms every order in writing within {v} hours of receipt.", "hours",
     "After I place an order, how long until I get written confirmation?"),
    ("ORDERS AND CANCELLATIONS", "STANDARD ORDERS", "CANCELLATION OF STANDARD ORDERS",
     "Standard orders may be cancelled free of charge up to {v} hours before dispatch.", "hours",
     "How late can I call off a regular purchase without paying anything?"),
    ("ORDERS AND CANCELLATIONS", "STANDARD ORDERS", "MINIMUM ORDER VALUE",
     "Parts orders below ${v} carry a small-order handling charge.", "amount",
     "What is the smallest spares purchase that avoids the extra handling fee?"),
    ("ORDERS AND CANCELLATIONS", "CUSTOM ORDERS", "CUSTOM CONFIGURATIONS",
     "Custom-configured compressors cannot be returned, and cancelling after production has "
     "started incurs a fee of {v}% of the order value.", "pct",
     "What does it cost to back out of a made-to-order machine once building has begun?"),
    ("ORDERS AND CANCELLATIONS", "CUSTOM ORDERS", "DEPOSITS",
     "A deposit of {v}% of the order value is due when a custom configuration is confirmed.",
     "pct", "How much do I have to pay up front for a bespoke unit?"),
    ("DELIVERY AND FREIGHT", "DELIVERY", "DELIVERY INSPECTION",
     "Freight damage must be reported within {v} hours of delivery.", "hours",
     "If a crate shows up smashed, how quickly must I tell you?"),
    ("DELIVERY AND FREIGHT", "DELIVERY", "PREPAID RETURN LABELS",
     "Orders above ${v} qualify for a prepaid return label.", "amount",
     "How big does my purchase need to be to get a free shipping label for sending it back?"),
    ("DELIVERY AND FREIGHT", "DELIVERY", "STORAGE BEFORE INSTALLATION",
     "Units stored before installation must be kept indoors and turned by hand every {v} days.",
     "days", "How often should I rotate the shaft of a machine that is waiting in a warehouse?"),
    ("RETURNS", "RETURN AUTHORISATION", "RMA NUMBERS",
     "A Return Merchandise Authorisation (RMA) number remains valid for {v} days after it is "
     "issued.", "days", "Once I've been given a return authorisation code, when does it expire?"),
    ("RETURNS", "RETURN WINDOWS", "UNOPENED ITEMS",
     "Unopened items in their original packaging may be returned within {v} days of delivery "
     "for a full refund.", "days",
     "How long do I have to send back something I never took out of the box?"),
    ("RETURNS", "RETURN WINDOWS", "OPENED ITEMS",
     "Opened but unused items may be returned within {v} days of delivery.", "days",
     "What's the deadline for handing back a part I unpacked but never fitted?"),
    ("RETURNS", "RETURN WINDOWS", "RESTOCKING FEE",
     "A restocking fee of {v}% of the invoice price applies to opened items.", "pct",
     "What cut do you keep when I send back something I've unpacked?"),
    ("RETURNS", "RETURN WINDOWS", "ELECTRICAL COMPONENTS",
     "Electrical components are returnable only if faulty and only within {v} days of "
     "delivery.", "days", "Within what time can I hand back a defective circuit board?"),
    ("RETURNS", "SPECIAL RETURNS", "CORE RETURNS",
     "Exchange air ends carry a core charge, and the old unit must be returned within {v} days "
     "to receive the core credit.", "days",
     "When I swap in a rebuilt screw element, how long do I have to ship the old one back to "
     "get my deposit refunded?"),
    ("RETURNS", "SPECIAL RETURNS", "OIL-CONTAMINATED PARTS",
     "Parts returned with oil inside are drained and cleaned for a charge of ${v}.", "amount",
     "What do you bill me if I send back a component that still has lubricant in it?"),
    ("RETURNS", "SPECIAL RETURNS", "INTERNATIONAL RETURNS",
     "Returns from outside the country of purchase are subject to a handling charge of {v}%.",
     "pct", "Is there an extra percentage fee if I ship a return back from abroad?"),
    ("WARRANTY", "WARRANTY START", "START DATE",
     "The warranty starts on the commissioning date or {v} days after shipment, whichever comes "
     "first.", "days", "If the machine sits uninstalled, when does the guarantee clock begin?"),
    ("WARRANTY", "WARRANTY START", "REGISTRATION",
     "Products must be registered within {v} days of commissioning to receive full warranty "
     "cover.", "days", "How soon after start-up do I have to sign the machine up to keep full "
                      "cover?"),
    ("WARRANTY", "EXCLUSIONS", "WEAR ITEMS",
     "Filters, belts and lubricants are wear items and are covered only if they fail within "
     "{v} operating hours.", "op_hours",
     "Are consumables covered if they give out early, and how early?"),
    ("WARRANTY", "EXTENDED WARRANTY", "PURCHASE WINDOW",
     "Extended warranty may be purchased within {v} days of commissioning.", "days",
     "How long after start-up can I still buy extra coverage?"),
    ("WARRANTY", "EXTENDED WARRANTY", "EXTENDED WARRANTY PRICE",
     "Each additional year of extended warranty costs {v}% of the list price of the unit.",
     "pct", "What does one more year of protection cost relative to the machine's price?"),
    ("WARRANTY CLAIMS", "FILING A CLAIM", "CLAIM DEADLINE",
     "Warranty claims must be filed within {v} days of discovering a defect.", "days",
     "Once I notice a fault, how long can I wait before reporting it for a free repair?"),
    ("WARRANTY CLAIMS", "FILING A CLAIM", "MAINTENANCE RECORDS",
     "Maintenance records covering at least the last {v} months must accompany every claim.",
     "months", "How far back do my service logs need to go when I ask for a free repair?"),
    ("WARRANTY CLAIMS", "REPAIRS", "LABOUR",
     "Labour for warranty repairs is free during the first {v} months of the warranty.",
     "months", "For how long do you pay for the technician's time on a guarantee fix?"),
    ("WARRANTY CLAIMS", "REPAIRS", "TRAVEL",
     "Technician travel beyond {v} km from the nearest service centre is charged to the "
     "customer.", "km", "How far will an engineer drive before I start paying for the trip?"),
    ("WARRANTY CLAIMS", "REPAIRS", "REPLACEMENT PARTS",
     "Parts fitted under warranty are covered for the rest of the original warranty or {v} "
     "days, whichever is longer.", "days",
     "If you swap a part under guarantee, what is the minimum time the new one is protected?"),
    ("WARRANTY CLAIMS", "REPAIRS", "LOAN UNITS",
     "A loan compressor is supplied free of charge when a warranty repair takes longer than "
     "{v} days.", "days", "If a fix drags on, after how long do I get a temporary machine?"),
    ("SERVICE CONTRACTS", "RESPONSE", "RESPONSE TIME",
     "Under a service contract, a technician will be on site within {v} hours of a breakdown "
     "call.", "hours",
     "With a maintenance plan, how fast will someone turn up when the unit breaks down?"),
    ("SERVICE CONTRACTS", "RESPONSE", "FIRMWARE UPDATES",
     "Controller firmware updates are free for {v} months after commissioning.", "months",
     "How long do I get free controller software upgrades?"),
    ("REFUNDS AND CREDITS", "PAYMENTS", "REFUND TIMING",
     "Refunds are paid to the original payment method within {v} days of the returned item "
     "passing inspection.", "days",
     "After you've checked my returned item, how soon will I see the money?"),
    ("REFUNDS AND CREDITS", "PAYMENTS", "INSPECTION OF RETURNS",
     "Returned items are inspected within {v} days of arrival at the warehouse.", "days",
     "How long does it take you to look over a sent-back item once it arrives?"),
    ("REFUNDS AND CREDITS", "PAYMENTS", "CREDIT NOTES",
     "Credit notes expire {v} months after the date of issue.", "months",
     "How long is store credit good for?"),
    ("DISPUTES", "APPEALS", "APPEAL DEADLINE",
     "A rejected warranty claim may be appealed in writing within {v} days of the decision.",
     "days", "If you turn down my claim, how long do I have to challenge it?"),
    ("DISPUTES", "APPEALS", "LATE PAYMENT",
     "Invoices unpaid {v} days after the due date are referred to collections.", "days",
     "How long after the due date before an unpaid bill goes to a debt collector?"),
]

# Value ranges per kind; generate.py draws distinct values so no two facts share a number.
VALUE_RANGES = {
    "hours": (12, 96), "days": (3, 120), "pct": (5, 45), "amount": (40, 900),
    "op_hours": (150, 900), "months": (6, 72), "km": (40, 250),
}
UNIT_WORDS = {"hours": "hours", "days": "days", "pct": "percent", "amount": "dollars",
              "op_hours": "operating hours", "months": "months", "km": "km"}

POLICY_FILLER = [
    "Halvard may ask for photographs before approving a request under this clause.",
    "Exceptions require written approval from the regional service manager.",
    "This clause applies to RS-Series compressors and genuine Halvard parts only.",
    "Requests must quote the order number and, where relevant, the machine serial number.",
    "Distributors apply the same terms to their own customers.",
    "Periods are counted in calendar days unless the clause says otherwise.",
]

# Handbook outline: chapters and their sections, in order. Clause numbers follow from it.
POLICY_OUTLINE = [
    ("INTRODUCTION", ["PURPOSE"]),
    ("ORDERS AND CANCELLATIONS", ["STANDARD ORDERS", "CUSTOM ORDERS"]),
    ("DELIVERY AND FREIGHT", ["DELIVERY"]),
    ("RETURNS", ["RETURN AUTHORISATION", "RETURN WINDOWS", "SPECIAL RETURNS"]),
    ("WARRANTY", ["WARRANTY START", "WARRANTY CLASSES", "EXCLUSIONS", "EXTENDED WARRANTY"]),
    ("WARRANTY CLAIMS", ["FILING A CLAIM", "REPAIRS"]),
    ("SERVICE CONTRACTS", ["RESPONSE"]),
    ("REFUNDS AND CREDITS", ["PAYMENTS"]),
    ("DISPUTES", ["APPEALS"]),
]

# Clauses without a planted fact, so the handbook reads like a real one.
POLICY_STATIC = {
    ("INTRODUCTION", "PURPOSE"): [
        ("PURPOSE OF THIS HANDBOOK", "This handbook sets out how Halvard Machine Works handles "
         "orders, returns, warranty claims and refunds for RS-Series compressors and parts."),
        ("DEFINITIONS", "Commissioning means the first start of the machine by a certified "
         "technician. Delivery means the date the goods are signed for at the customer site."),
    ],
    ("RETURNS", "RETURN AUTHORISATION"): [
        ("RETURN PACKAGING", "Returned goods must be packed so that they cannot move in transit. "
         "Damage caused by poor packaging is charged to the customer."),
    ],
    ("WARRANTY", "EXCLUSIONS"): [
        ("UNAPPROVED LUBRICANTS", "Use of lubricants not approved by Halvard voids the warranty "
         "on the air end."),
        ("NON-CERTIFIED REPAIRS", "Repairs carried out by technicians who are not certified by "
         "Halvard void the warranty on the affected assembly."),
    ],
}

WARRANTY_CLASS_SENTENCE = ("Class {wc} components are covered for {v} months from the warranty "
                           "start date.")

# ---------------------------------------------------------------- unanswerable questions
# Topics the corpus never mentions. generate.py checks that none of `absent` occurs anywhere.
OFF_CORPUS = [
    ("What is the noise level of the RS-55 in decibels?", ["decibel", "noise", "db(a)"]),
    ("Can I pay for spare parts in monthly instalments?", ["instalment", "installment"]),
    ("Does the warranty carry over to a new owner if I sell the compressor?", ["owner"]),
    ("Which colours can the compressor enclosure be ordered in?", ["colour", "color"]),
    ("Is there a smartphone app for monitoring the compressor remotely?",
     ["smartphone", "mobile"]),
    ("How much does an operator training course cost?", ["training", "course"]),
]
