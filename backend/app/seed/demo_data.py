from datetime import datetime, timedelta
import json
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, DepartmentType
from app.models.section import RailwaySection
from app.models.resource import Resource, ResourceType
from app.models.request import MaintenanceRequest, MaintenanceType, AssetCriticality, UrgencyLevel, RequestStatus
from app.models.train import TrainSchedule, TrainType
from app.models.disruption import Disruption, DisruptionType, DisruptionSeverity
from app.models.audit import AuditLog
from app.utils.security import get_password_hash
from app.ml.priority_model import priority_engine
from app.optimization.scheduler import optimizer_scheduler

def seed_database(db: Session):
    # Check if data already exists
    if db.query(User).first():
        return

    print("Initializing RailBlockSetu Database with realistic Indian Railways demo dataset...")

    # 1. Create Users
    users_data = [
        {
            "username": "admin",
            "email": "admin@railblocksetu.gov.in",
            "full_name": "Rajesh Sharma (Chief Operations Manager)",
            "password": "admin123",
            "role": UserRole.ADMIN,
            "department": DepartmentType.ALL,
        },
        {
            "username": "ops_officer",
            "email": "ops@railblocksetu.gov.in",
            "full_name": "Amitabh Verma (Senior Divisional Operations Manager)",
            "password": "ops123",
            "role": UserRole.OPERATIONS_OFFICER,
            "department": DepartmentType.OPERATIONS,
        },
        {
            "username": "engg_officer",
            "email": "engg@railblocksetu.gov.in",
            "full_name": "Suresh Chandra (Senior Divisional Engineer / Track)",
            "password": "engg123",
            "role": UserRole.DEPARTMENT_OFFICER,
            "department": DepartmentType.ENGINEERING,
        },
        {
            "username": "trd_officer",
            "email": "trd@railblocksetu.gov.in",
            "full_name": "Deepak Khurana (Divisional Electrical Engineer / TRD)",
            "password": "trd123",
            "role": UserRole.DEPARTMENT_OFFICER,
            "department": DepartmentType.TRD,
        },
        {
            "username": "st_officer",
            "email": "st@railblocksetu.gov.in",
            "full_name": "Pooja Singhania (Senior Divisional Signal & Telecom Engineer)",
            "password": "st123",
            "role": UserRole.DEPARTMENT_OFFICER,
            "department": DepartmentType.ST,
        },
    ]

    users_map = {}
    for ud in users_data:
        pwd = ud.pop("password")
        u = User(**ud, hashed_password=get_password_hash(pwd), is_active=True)
        db.add(u)
        db.commit()
        db.refresh(u)
        users_map[u.username] = u

    # 2. Create Railway Sections (Delhi Division Trunk Lines)
    sections_data = [
        {
            "section_code": "NDLS-GZB",
            "section_name": "New Delhi to Ghaziabad Trunk Corridor",
            "division": "Delhi",
            "zone": "Northern Railway",
            "start_km": 0.0,
            "end_km": 25.4,
            "track_count": "QUAD",
            "electrification_type": "25kV_AC",
            "max_speed_kmh": 130,
            "signaling_system": "Automatic Block Signaling (ABS) with KAVACH",
            "traffic_density": "VERY_HIGH"
        },
        {
            "section_code": "NZM-TKD",
            "section_name": "Hazrat Nizamuddin to Tuglakabad Freight & Main",
            "division": "Delhi",
            "zone": "Northern Railway",
            "start_km": 7.2,
            "end_km": 22.0,
            "track_count": "QUAD",
            "electrification_type": "25kV_AC",
            "max_speed_kmh": 130,
            "signaling_system": "Automatic Block Signaling (ABS) with KAVACH",
            "traffic_density": "VERY_HIGH"
        },
        {
            "section_code": "TKD-PWL",
            "section_name": "Tuglakabad to Palwal Semi-High Speed Line",
            "division": "Delhi",
            "zone": "Northern Railway",
            "start_km": 22.0,
            "end_km": 60.6,
            "track_count": "QUAD",
            "electrification_type": "25kV_AC",
            "max_speed_kmh": 160,
            "signaling_system": "Automatic Block Signaling (ABS) with KAVACH",
            "traffic_density": "VERY_HIGH"
        },
        {
            "section_code": "GZB-ALJN",
            "section_name": "Ghaziabad to Aligarh East-Coast Feeder",
            "division": "Delhi",
            "zone": "Northern Railway",
            "start_km": 25.4,
            "end_km": 131.5,
            "track_count": "DOUBLE",
            "electrification_type": "25kV_AC",
            "max_speed_kmh": 130,
            "signaling_system": "Multi-Aspect Color Light Signaling (MACLS)",
            "traffic_density": "HIGH"
        },
        {
            "section_code": "NDLS-PNP",
            "section_name": "New Delhi to Panipat Northern Gateway",
            "division": "Delhi",
            "zone": "Northern Railway",
            "start_km": 0.0,
            "end_km": 88.9,
            "track_count": "DOUBLE",
            "electrification_type": "25kV_AC",
            "max_speed_kmh": 130,
            "signaling_system": "Automatic Block Signaling (ABS)",
            "traffic_density": "HIGH"
        }
    ]

    sec_map = {}
    for sd in sections_data:
        sec = RailwaySection(**sd)
        db.add(sec)
        db.commit()
        db.refresh(sec)
        sec_map[sec.section_code] = sec

    # 3. Create Resources
    resources_data = [
        # Heavy Machinery
        {"resource_type": ResourceType.MACHINERY, "name": "Plasser CSM-952 Continuous Track Tamping Machine", "code": "CSM-952", "department": "Engineering", "total_quantity": 2.0, "available_quantity": 1.0, "unit": "Machine", "specifications": "High-output 3-sleeper tamping with laser alignment", "base_station": "Ghaziabad Track Depot"},
        {"resource_type": ResourceType.MACHINERY, "name": "Plasser BCM-12 Ballast Cleaning Machine", "code": "BCM-12", "department": "Engineering", "total_quantity": 1.0, "available_quantity": 1.0, "unit": "Machine", "specifications": "Excavates, screens and relaid ballast at 650 m3/hr", "base_station": "Tuglakabad Track Machine Base"},
        {"resource_type": ResourceType.MACHINERY, "name": "8-Wheeler DETC Tower Wagon (High Voltage)", "code": "TW-04", "department": "TRD", "total_quantity": 3.0, "available_quantity": 2.0, "unit": "Machine", "specifications": "Diesel-electric inspection tower car with pantograph test unit", "base_station": "Hazrat Nizamuddin OHE Depot"},
        {"resource_type": ResourceType.MACHINERY, "name": "UNIMAT-08 Point & Crossing Switch Tamping Unit", "code": "UNIMAT-08", "department": "Engineering", "total_quantity": 1.0, "available_quantity": 1.0, "unit": "Machine", "specifications": "Specialized heavy turnout tamping machine", "base_station": "New Delhi Marshalling Yard"},
        {"resource_type": ResourceType.MACHINERY, "name": "Signal Cable Trenching & Fault Locator Vehicle", "code": "SFL-01", "department": "S&T", "total_quantity": 2.0, "available_quantity": 2.0, "unit": "Vehicle", "specifications": "Time-Domain Reflectometer & cable locator", "base_station": "Delhi Central Signal Workshop"},
        
        # Staff Gang Personnel
        {"resource_type": ResourceType.STAFF, "name": "Permanent-Way Track Gang Unit #4", "code": "PWAY-GANG-04", "department": "Engineering", "total_quantity": 40.0, "available_quantity": 32.0, "unit": "Personnel", "specifications": "Certified keymen, mates, trackmen with welding clearance", "base_station": "Ghaziabad Subdivision"},
        {"resource_type": ResourceType.STAFF, "name": "OHE Overhead Traction Linemen Squad", "code": "TRD-CREW-02", "department": "TRD", "total_quantity": 25.0, "available_quantity": 21.0, "unit": "Personnel", "specifications": "25kV live/isolated electrical safety certified linesmen", "base_station": "Hazrat Nizamuddin Depot"},
        {"resource_type": ResourceType.STAFF, "name": "Electronic Interlocking Signal Maintainers", "code": "ST-CREW-01", "department": "S&T", "total_quantity": 18.0, "available_quantity": 15.0, "unit": "Personnel", "specifications": "Kyosan / Siemens Electronic Interlocking certified engineers", "base_station": "New Delhi Central S&T Control"},

        # Critical Materials & Spares
        {"resource_type": ResourceType.MATERIAL, "name": "60kg UIC 880 Grade Pre-Stressed Concrete Sleepers", "code": "PSC-60KG", "department": "Engineering", "total_quantity": 800.0, "available_quantity": 650.0, "unit": "Sleepers", "specifications": "RDSO approved heavy axle concrete sleepers", "base_station": "Tuglakabad Stores Depot"},
        {"resource_type": ResourceType.MATERIAL, "name": "107 sq. mm Hard Drawn Grooved Copper Contact Wire", "code": "CW-107", "department": "TRD", "total_quantity": 3000.0, "available_quantity": 2400.0, "unit": "Meters", "specifications": "High-conductivity copper wire for 160 km/h OHE", "base_station": "Nizamuddin TRD Stores"},
        {"resource_type": ResourceType.MATERIAL, "name": "Point Machine Siemens 24V DC Throw Drive Motor", "code": "PM-SIEMENS", "department": "S&T", "total_quantity": 20.0, "available_quantity": 14.0, "unit": "Units", "specifications": "143mm stroke point operating motor with detection contacts", "base_station": "Delhi Central S&T Stores"},
        {"resource_type": ResourceType.MATERIAL, "name": "Glued Insulated Rail Joints (G3L 60kg)", "code": "IRJ-60KG", "department": "S&T", "total_quantity": 50.0, "available_quantity": 42.0, "unit": "Joints", "specifications": "6-bolt high strength epoxy bonded insulated joints", "base_station": "Ghaziabad Signal Stores"},
        {"resource_type": ResourceType.MATERIAL, "name": "Track Ballast 50mm Machine Crushed Granite", "code": "BAL-50MM", "department": "Engineering", "total_quantity": 1500.0, "available_quantity": 1200.0, "unit": "m3", "specifications": "Abrasion index < 20% granite ballast", "base_station": "Faridabad Ballast Depot"}
    ]

    for rd in resources_data:
        r = Resource(**rd)
        db.add(r)
    db.commit()

    # 4. Create Train Schedules
    trains_data = [
        {"train_number": "22436", "train_name": "Vande Bharat Express (NDLS-BSB)", "train_type": TrainType.VANDE_BHARAT, "origin": "New Delhi", "destination": "Varanasi", "priority_level": 1, "section_id": sec_map["NDLS-GZB"].id, "scheduled_entry_time": "06:00", "scheduled_exit_time": "06:30", "typical_delay_minutes": 2},
        {"train_number": "12302", "train_name": "Howrah Rajdhani Express", "train_type": TrainType.RAJDHANI, "origin": "New Delhi", "destination": "Howrah", "priority_level": 1, "section_id": sec_map["NDLS-GZB"].id, "scheduled_entry_time": "16:50", "scheduled_exit_time": "17:25", "typical_delay_minutes": 5},
        {"train_number": "12002", "train_name": "Bhopal Shatabdi Express", "train_type": TrainType.SHATABDI, "origin": "New Delhi", "destination": "Rani Kamlapati", "priority_level": 2, "section_id": sec_map["TKD-PWL"].id, "scheduled_entry_time": "06:35", "scheduled_exit_time": "07:15", "typical_delay_minutes": 0},
        {"train_number": "12424", "train_name": "Dibrugarh Rajdhani Express", "train_type": TrainType.RAJDHANI, "origin": "New Delhi", "destination": "Dibrugarh", "priority_level": 1, "section_id": sec_map["GZB-ALJN"].id, "scheduled_entry_time": "16:10", "scheduled_exit_time": "17:30", "typical_delay_minutes": 8},
        {"train_number": "12952", "train_name": "Mumbai Central Tejas Rajdhani", "train_type": TrainType.RAJDHANI, "origin": "New Delhi", "destination": "Mumbai Central", "priority_level": 1, "section_id": sec_map["NZM-TKD"].id, "scheduled_entry_time": "17:00", "scheduled_exit_time": "17:35", "typical_delay_minutes": 3},
        {"train_number": "BOXN-781", "train_name": "Coal Rake Dedicated Freight", "train_type": TrainType.FREIGHT, "origin": "Tuglakabad Yard", "destination": "Panipat Thermal Power", "priority_level": 5, "section_id": sec_map["NDLS-PNP"].id, "scheduled_entry_time": "02:15", "scheduled_exit_time": "04:10", "typical_delay_minutes": 15},
    ]

    for td in trains_data:
        tr = TrainSchedule(**td)
        db.add(tr)
    db.commit()

    # 5. Create Realistic Maintenance Requests
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    requests_data = [
        {
            "request_id": "REQ-ENG-2026-001",
            "task_title": "Track Geometry Tamping & Track Packing (Km 14.2 to 19.8)",
            "description": "Continuous mechanized tamping to eliminate twist and cross-level deviations detected by Track Recording Car (TRC). Necessary to prevent 30 km/h caution order on UP Main Line.",
            "department": "Engineering",
            "railway_division": "Delhi",
            "railway_section": "NDLS-GZB",
            "section_id": sec_map["NDLS-GZB"].id,
            "asset_id": "TRK-NDLS-GZB-UP-KM16",
            "asset_type": "Track",
            "maintenance_type": MaintenanceType.PREVENTIVE,
            "required_start_date": now + timedelta(hours=14),
            "deadline": now + timedelta(days=2),
            "estimated_duration": 3.0,
            "required_staff": 8,
            "required_machinery": json.dumps(["CSM-952"]),
            "required_materials": json.dumps(["PSC-60KG"]),
            "safety_requirements": json.dumps(["Track possession memo", "Banner flag at 600m", "Lookout man"]),
            "task_dependencies": json.dumps([]),
            "asset_criticality": AssetCriticality.CRITICAL,
            "urgency_level": UrgencyLevel.URGENT,
            "current_status": RequestStatus.SUBMITTED,
            "created_by_id": users_map["engg_officer"].id,
        },
        {
            "request_id": "REQ-TRD-2026-002",
            "task_title": "25kV OHE Contact Wire Re-tensioning & Cantilever Tuning",
            "description": "Thermal expansion sag rectification on Down line cantilever mast #120/14. Replace worn contact clips and check dropper staggering for 160 km/h Vande Bharat compliance.",
            "department": "TRD",
            "railway_division": "Delhi",
            "railway_section": "NZM-TKD",
            "section_id": sec_map["NZM-TKD"].id,
            "asset_id": "OHE-NZM-TKD-DN-MST120",
            "asset_type": "OHE_Traction",
            "maintenance_type": MaintenanceType.CORRECTIVE,
            "required_start_date": now + timedelta(hours=18),
            "deadline": now + timedelta(days=2),
            "estimated_duration": 2.5,
            "required_staff": 6,
            "required_machinery": json.dumps(["TW-04"]),
            "required_materials": json.dumps(["CW-107"]),
            "safety_requirements": json.dumps(["25kV Power Block permit", "Station Master isolation memo", "Earthing rods"]),
            "task_dependencies": json.dumps([]),
            "asset_criticality": AssetCriticality.HIGH,
            "urgency_level": UrgencyLevel.URGENT,
            "current_status": RequestStatus.SUBMITTED,
            "created_by_id": users_map["trd_officer"].id,
        },
        {
            "request_id": "REQ-ST-2026-003",
            "task_title": "Point Machine 104A/B Overhaul & SSDAC Sensor Calibration",
            "description": "Quarterly overhaul of facing turnout switch machine at Ghaziabad entry interlocking. Test detection contact clearances and reset redundant axle counter transducers.",
            "department": "S&T",
            "railway_division": "Delhi",
            "railway_section": "NDLS-GZB",
            "section_id": sec_map["NDLS-GZB"].id,
            "asset_id": "PNT-GZB-104AB",
            "asset_type": "Point_Machine",
            "maintenance_type": MaintenanceType.PREVENTIVE,
            "required_start_date": now + timedelta(hours=22),
            "deadline": now + timedelta(days=3),
            "estimated_duration": 2.0,
            "required_staff": 5,
            "required_machinery": json.dumps(["SFL-01"]),
            "required_materials": json.dumps(["PM-SIEMENS", "IRJ-60KG"]),
            "safety_requirements": json.dumps(["Disconnection Memo S&T (T-351)", "Station Master clamp locking"]),
            "task_dependencies": json.dumps(["REQ-ENG-2026-001"]),
            "asset_criticality": AssetCriticality.HIGH,
            "urgency_level": UrgencyLevel.ROUTINE,
            "current_status": RequestStatus.SUBMITTED,
            "created_by_id": users_map["st_officer"].id,
        },
        {
            "request_id": "REQ-ENG-2026-004",
            "task_title": "Ballast Deep Screening by BCM Machine (Km 42 to 46)",
            "description": "Full ballast cleaning and silt extraction to eliminate track mud pumping and water logging under sleeper seats on Palwal high-speed corridor.",
            "department": "Engineering",
            "railway_division": "Delhi",
            "railway_section": "TKD-PWL",
            "section_id": sec_map["TKD-PWL"].id,
            "asset_id": "TRK-TKD-PWL-KM44",
            "asset_type": "Track",
            "maintenance_type": MaintenanceType.OVERHAUL,
            "required_start_date": now + timedelta(hours=28),
            "deadline": now + timedelta(days=4),
            "estimated_duration": 4.0,
            "required_staff": 12,
            "required_machinery": json.dumps(["BCM-12"]),
            "required_materials": json.dumps(["BAL-50MM", "PSC-60KG"]),
            "safety_requirements": json.dumps(["Both lines speed restriction 20 km/h", "Temporary neutral section"]),
            "task_dependencies": json.dumps([]),
            "asset_criticality": AssetCriticality.CRITICAL,
            "urgency_level": UrgencyLevel.EMERGENCY,
            "current_status": RequestStatus.SUBMITTED,
            "created_by_id": users_map["engg_officer"].id,
        },
        {
            "request_id": "REQ-TRD-2026-005",
            "task_title": "Traction Substation 132/25kV Transformer Bushing Test",
            "description": "Annual insulation resistance and Tan-Delta diagnostic testing of 30MVA traction power transformer at Tuglakabad sub-station.",
            "department": "TRD",
            "railway_division": "Delhi",
            "railway_section": "TKD-PWL",
            "section_id": sec_map["TKD-PWL"].id,
            "asset_id": "TSS-TKD-TR1",
            "asset_type": "Substation",
            "maintenance_type": MaintenanceType.PREVENTIVE,
            "required_start_date": now + timedelta(hours=36),
            "deadline": now + timedelta(days=5),
            "estimated_duration": 3.5,
            "required_staff": 4,
            "required_machinery": json.dumps([]),
            "required_materials": json.dumps([]),
            "safety_requirements": json.dumps(["State Grid coordination", "TSS Busbar isolator opening"]),
            "task_dependencies": json.dumps([]),
            "asset_criticality": AssetCriticality.MEDIUM,
            "urgency_level": UrgencyLevel.ROUTINE,
            "current_status": RequestStatus.SUBMITTED,
            "created_by_id": users_map["trd_officer"].id,
        },
        {
            "request_id": "REQ-ST-2026-006",
            "task_title": "KAVACH RFID Tag Alignment & Trackside Unit Replacement",
            "description": "Re-alignment of track sleeper RFID transponders and diagnostic check of Stationary Kavach Radio Unit (RU) antenna at Km 68 on Aligarh route.",
            "department": "S&T",
            "railway_division": "Delhi",
            "railway_section": "GZB-ALJN",
            "section_id": sec_map["GZB-ALJN"].id,
            "asset_id": "KAVACH-ALJN-KM68",
            "asset_type": "KAVACH_ATP",
            "maintenance_type": MaintenanceType.CORRECTIVE,
            "required_start_date": now + timedelta(hours=48),
            "deadline": now + timedelta(days=6),
            "estimated_duration": 2.0,
            "required_staff": 4,
            "required_machinery": json.dumps([]),
            "required_materials": json.dumps([]),
            "safety_requirements": json.dumps(["Pilot locomotive test run", "Signal telecom log memo"]),
            "task_dependencies": json.dumps([]),
            "asset_criticality": AssetCriticality.HIGH,
            "urgency_level": UrgencyLevel.URGENT,
            "current_status": RequestStatus.SUBMITTED,
            "created_by_id": users_map["st_officer"].id,
        }
    ]

    for req_dict in requests_data:
        # Calculate AI Priority using ML model
        ml_prediction = priority_engine.predict(req_dict)
        
        req = MaintenanceRequest(
            **req_dict,
            ai_priority_score=ml_prediction["ai_priority_score"],
            ai_risk_factor=ml_prediction["ai_risk_factor"],
            ai_explanation=ml_prediction["ai_explanation"],
            readiness_score=85.0
        )
        db.add(req)
    db.commit()

    # 6. Create Initial Sample Disruption (for demonstration)
    disruption = Disruption(
        disruption_code="DIS-2026-DEL-01",
        title="OHE Dropper Breakdown & Contact Wire Sag at Km 14/8",
        disruption_type=DisruptionType.OHE_BREAKDOWN,
        section_id=sec_map["NZM-TKD"].id,
        affected_from=now + timedelta(hours=16),
        affected_until=now + timedelta(hours=21),
        severity=DisruptionSeverity.CRITICAL,
        impact_description="Severe dropper snapping due to excessive pantograph friction. Down line speed restricted to 0 km/h until emergency tower wagon repairs complete.",
        is_active=True,
        replan_triggered=False,
        affected_blocks_count=0,
        preserved_blocks_count=0
    )
    db.add(disruption)
    db.commit()

    # 7. Add Initial Audit Activity Feed Entries
    initial_audits = [
        AuditLog(user_name="System", role="SYSTEM", action="SYSTEM_INIT", department="All", badge_type="info", details="RailBlockSetu Decision Support Platform initialized for Delhi Division."),
        AuditLog(user_name="Rajesh Sharma", role="ADMIN", action="CONFIGURE_PARAMETERS", department="All", badge_type="info", details="KAVACH & ABS Automatic block signaling constraints loaded into CP-SAT solver."),
        AuditLog(user_name="Suresh Chandra", role="DEPARTMENT_OFFICER", action="SUBMIT_REQUEST", department="Engineering", badge_type="success", details="Submitted request REQ-ENG-2026-001 (Track Tamping Km 14-19). ML estimated priority: 92.4."),
        AuditLog(user_name="Deepak Khurana", role="DEPARTMENT_OFFICER", action="SUBMIT_REQUEST", department="TRD", badge_type="success", details="Submitted request REQ-TRD-2026-002 (OHE 25kV Cantilever tuning)."),
        AuditLog(user_name="Amitabh Verma", role="OPERATIONS_OFFICER", action="TRAIN_TRAFFIC_SYNC", department="Operations", badge_type="info", details="Synced 6 passenger & freight timetables including Vande Bharat & Rajdhani."),
    ]
    for aud in initial_audits:
        db.add(aud)
    db.commit()

    # 8. Run an initial CP-SAT optimization to seed proposed blocks!
    print("Running initial Google OR-Tools CP-SAT optimization on demo dataset...")
    optimizer_scheduler.run_optimization(db=db, horizon_hours=72)
    print("Demo dataset seeded successfully!")
