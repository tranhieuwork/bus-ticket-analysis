import os
import numpy as np
import pandas as pd

SEED = 42
START, END = "2024-01-01", "2025-12-31"
N_BOOKINGS_TARGET = 320_000      # so booking sinh ra truoc khi bi gioi han boi suc chua ghe
N_CUSTOMER_POOL = 200_000
OUT_DIR = "data"

rng = np.random.default_rng(SEED)
os.makedirs(OUT_DIR, exist_ok=True)

# =====================================================================
# 1. DIM_DATE  (kem mua vu, ngay le)
# =====================================================================
dates = pd.date_range(START, END)
dim_date = pd.DataFrame({"date": dates})
dim_date["year"] = dim_date.date.dt.year
dim_date["quarter"] = "Q" + dim_date.date.dt.quarter.astype(str)
dim_date["month"] = dim_date.date.dt.month
dim_date["month_name"] = dim_date.date.dt.strftime("%b")
dim_date["year_month"] = dim_date.date.dt.strftime("%Y-%m")
dim_date["week_of_year"] = dim_date.date.dt.isocalendar().week.astype(int)
dim_date["day_of_week"] = dim_date.date.dt.weekday + 1          # 1 = Thu 2 ... 7 = CN
dim_date["day_name"] = dim_date.date.dt.strftime("%a")
dim_date["is_weekend"] = dim_date.date.dt.weekday >= 5

# (ten, tu ngay, den ngay, he so luong cau, he so gia ve)
PEAKS = [
    ("Tet 2024",            "2024-02-02", "2024-02-16", 2.2, 1.35),
    ("Tet 2025",            "2025-01-21", "2025-02-04", 2.2, 1.35),
    ("Le 30/4-1/5 2024",    "2024-04-27", "2024-05-01", 1.6, 1.15),
    ("Le 30/4-1/5 2025",    "2025-04-26", "2025-05-01", 1.6, 1.15),
    ("Quoc khanh 2/9 2024", "2024-08-30", "2024-09-03", 1.5, 1.15),
    ("Quoc khanh 2/9 2025", "2025-08-29", "2025-09-02", 1.5, 1.15),
]
dim_date["holiday_name"] = ""
dim_date["demand_mult"] = 1.0
dim_date["price_mult"] = 1.0

# He so mua he (T6-T8)
summer = dim_date.month.isin([6, 7, 8])
dim_date.loc[summer, "demand_mult"] *= 1.25
dim_date.loc[summer, "price_mult"] *= 1.05
# He so cuoi tuan: Thu 6, Thu 7, Chu nhat
dim_date.loc[dim_date.day_of_week.isin([5, 7]), "demand_mult"] *= 1.2
dim_date.loc[dim_date.day_of_week == 6, "demand_mult"] *= 1.1
# Le / Tet
for name, s, e, dm, pm in PEAKS:
    m = (dim_date.date >= s) & (dim_date.date <= e)
    dim_date.loc[m, "holiday_name"] = name
    dim_date.loc[m, "demand_mult"] *= dm
    dim_date.loc[m, "price_mult"] *= pm
dim_date["is_holiday_peak"] = dim_date.holiday_name != ""
dim_date["season"] = np.where(summer, "Mua he", np.where(dim_date.is_holiday_peak, "Le/Tet", "Binh thuong"))
# Xu huong tang truong ~35% sau 2 nam
t = np.arange(len(dim_date)) / (len(dim_date) - 1)
dim_date["demand_mult"] *= 1 + 0.35 * t

# =====================================================================
# 2. DIM_ROUTE
# =====================================================================
route_rows = [
    # origin,        destination,    km,  gio, gia_goc, do_pho_bien
    ("Hà Nội",      "Hải Phòng",    120, 2.5, 120_000, 1.6),
    ("Hà Nội",      "Sa Pa",        320, 6.0, 300_000, 1.2),   # tuyen "co van de": ty le huy cao
    ("Hà Nội",      "Vinh",         300, 5.5, 250_000, 1.0),
    ("TP.HCM",      "Đà Lạt",       300, 7.0, 300_000, 1.8),
    ("TP.HCM",      "Vũng Tàu",     100, 2.5, 150_000, 2.0),
    ("TP.HCM",      "Cần Thơ",      170, 3.5, 170_000, 1.7),
    ("Đà Nẵng",     "Huế",          100, 2.5, 120_000, 0.9),
    ("Hà Nội",      "Thanh Hóa",    150, 3.0, 150_000, 1.0),
    ("TP.HCM",      "Nha Trang",    430, 9.0, 380_000, 1.4),
    ("TP.HCM",      "Phan Thiết",   200, 4.0, 200_000, 1.2),
    ("Hà Nội",      "Nam Định",      90, 2.0, 100_000, 0.8),
    ("Đà Nẵng",     "Hội An",        30, 1.0,  70_000, 0.6),
    ("TP.HCM",      "Buôn Ma Thuột",350, 8.0, 330_000, 0.8),
    ("Hà Nội",      "Ninh Bình",     95, 2.0, 110_000, 1.1),
    ("TP.HCM",      "Quy Nhơn",     650,12.0, 450_000, 0.7),
    ("Huế",         "Hà Nội",       680,13.0, 450_000, 0.6),
    ("Hà Nội",      "Hạ Long",      160, 3.0, 160_000, 1.3),
    ("TP.HCM",      "Cà Mau",       330, 7.0, 300_000, 0.7),
    ("Cần Thơ",     "TP.HCM",       170, 3.5, 170_000, 1.5),
    ("Hà Nội",      "Đà Nẵng",      770,14.0, 500_000, 1.0),
]
dim_route = pd.DataFrame(route_rows, columns=["origin", "destination", "distance_km",
                                              "duration_hours", "base_price", "popularity"])
dim_route.insert(0, "route_id", np.arange(1, len(dim_route) + 1))
dim_route["route_name"] = dim_route.origin + " → " + dim_route.destination
SAPA_ID = int(dim_route.loc[dim_route.destination == "Sa Pa", "route_id"].iloc[0])
QUYNHON_ID = int(dim_route.loc[dim_route.destination == "Quy Nhơn", "route_id"].iloc[0])

# =====================================================================
# 3. DIM_OPERATOR
# =====================================================================
op_names = ["Sao Việt", "Bình An", "Thiên Long", "Hải Âu", "Xuân Mai", "Đại Nam", "Kim Mã", "Minh Tâm",
            "Hải Vân", "Tân Phát", "Phúc Lộc", "Việt Thành", "An Phú", "Gia Hưng", "Lam Sơn", "Thái Bình",
            "Hoa Mai", "Đông Dương", "Bắc Nam", "Trường Sinh", "Ngọc Lan", "Quang Huy", "Thành Công",
            "Mộc Châu", "Cửu Long", "Hồng Hà", "Vạn Xuân", "Nam Phương", "Tây Đô", "Long Biên"]
N_OP = len(op_names)
dim_operator = pd.DataFrame({
    "operator_id": np.arange(1, N_OP + 1),
    "operator_name": ["Nhà xe " + n for n in op_names],
    "bus_type": rng.choice(["Giường nằm", "Limousine", "Ghế ngồi"], N_OP, p=[.5, .3, .2]),
    "rating": rng.normal(4.3, .3, N_OP).clip(3.6, 4.9).round(1),
    "commission_rate": rng.choice([.08, .10, .12], N_OP, p=[.3, .5, .2]),
    "join_date": pd.to_datetime("2016-01-01") + pd.to_timedelta(rng.integers(0, 365 * 8, N_OP), unit="D"),
})
dim_operator["total_seats"] = dim_operator.bus_type.map({"Ghế ngồi": 45, "Giường nằm": 34, "Limousine": 22})
dim_operator["popularity"] = rng.lognormal(0, 0.5, N_OP)
# INSIGHT: nha xe so 7 rating thap nhung ban rat nhieu ve
LOW_RATED_OP = 7
dim_operator.loc[dim_operator.operator_id == LOW_RATED_OP, ["rating", "popularity"]] = [3.4, 3.0]

# =====================================================================
# 4. DIM_CHANNEL
# =====================================================================
dim_channel = pd.DataFrame({
    "channel_id": [1, 2, 3, 4],
    "channel_name": ["App Android", "App iOS", "Web", "Đối tác"],
    "channel_group": ["App", "App", "Web", "Partner"],
})
CHANNEL_P = [.35, .25, .25, .15]
CHANNEL_CANCEL_EXTRA = {1: 0.0, 2: -0.005, 3: 0.04, 4: 0.01}   # INSIGHT: Web huy nhieu hon

# =====================================================================
# 5. DIM_VOUCHER
# =====================================================================
dim_voucher = pd.DataFrame([
    # id, code,         type,      value,   start,        end,          xac suat dung
    (1, "VEX5",        "percent",  0.05, "2024-01-01", "2025-12-31", 0.10),
    (2, "WELCOME50K",  "fixed",   50000, "2024-01-01", "2025-12-31", 0.05),
    (3, "TET15_2024",  "percent",  0.15, "2024-01-20", "2024-02-09", 0.45),
    (4, "HE10_2024",   "percent",  0.10, "2024-06-01", "2024-08-31", 0.30),
    (5, "TET15_2025",  "percent",  0.15, "2025-01-08", "2025-01-28", 0.45),
    (6, "HE10_2025",   "percent",  0.10, "2025-06-01", "2025-08-31", 0.30),
    (7, "FLASH30K",    "fixed",   30000, "2025-11-01", "2025-11-30", 0.40),
], columns=["voucher_id", "voucher_code", "discount_type", "discount_value",
            "start_date", "end_date", "use_prob"])
dim_voucher["start_date"] = pd.to_datetime(dim_voucher.start_date)
dim_voucher["end_date"] = pd.to_datetime(dim_voucher.end_date)
dim_voucher["budget"] = rng.choice([200, 300, 500], len(dim_voucher)) * 1_000_000

# =====================================================================
# 6. FACT_TRIPS  (moi dong = 1 chuyen xe)
# =====================================================================
# 6a. Cap (nha xe, tuyen): moi tuyen co it nhat 1 nha xe, moi nha xe chay 2-3 tuyen
pairs = set()
route_ids = dim_route.route_id.to_numpy()
op_ids = dim_operator.operator_id.to_numpy()
shuffled_ops = rng.permutation(op_ids)
for i, r in enumerate(route_ids):                      # dam bao moi tuyen co nha xe
    pairs.add((int(shuffled_ops[i % N_OP]), int(r)))
route_p = (dim_route.popularity / dim_route.popularity.sum()).to_numpy()
for o in op_ids:                                       # moi nha xe them 1-2 tuyen theo do pho bien
    for r in rng.choice(route_ids, size=rng.integers(1, 3), replace=False, p=route_p):
        pairs.add((int(o), int(r)))
pairs = sorted(pairs)
DEPART_HOURS = [6, 7, 8, 12, 19, 20, 21, 22]

# 6b. Lich chay: moi cap chay 2-3 ngay/tuan, chay moi ngay vao cao diem
trip_rows = []
peak_dates = set(dim_date.loc[dim_date.is_holiday_peak, "date"])
for o, r in pairs:
    run_days = set(rng.choice(7, size=rng.integers(2, 4), replace=False).tolist())
    hour = int(rng.choice(DEPART_HOURS))
    for d in dates:
        if d.weekday() in run_days or d in peak_dates:
            trip_rows.append((o, r, d, hour))
fact_trips = pd.DataFrame(trip_rows, columns=["operator_id", "route_id", "departure_date", "departure_hour"])
fact_trips.insert(0, "trip_id", np.arange(1, len(fact_trips) + 1))
fact_trips["departure_datetime"] = fact_trips.departure_date + pd.to_timedelta(fact_trips.departure_hour, unit="h")

fact_trips = (fact_trips
              .merge(dim_operator[["operator_id", "bus_type", "total_seats", "popularity"]], on="operator_id")
              .merge(dim_route[["route_id", "base_price", "popularity"]].rename(columns={"popularity": "route_pop"}),
                     on="route_id")
              .merge(dim_date[["date", "demand_mult", "price_mult"]], left_on="departure_date", right_on="date")
              .drop(columns="date")
              .sort_values("trip_id").reset_index(drop=True))

bus_mult = fact_trips.bus_type.map({"Ghế ngồi": 0.85, "Giường nằm": 1.0, "Limousine": 1.35})
fare = fact_trips.base_price * bus_mult * fact_trips.price_mult * rng.uniform(0.95, 1.05, len(fact_trips))
fact_trips["base_fare"] = (np.round(fare / 10_000) * 10_000).clip(lower=50_000).astype(int)

# =====================================================================
# 7. FACT_BOOKINGS
# =====================================================================
# 7a. Chon chuyen xe cho tung booking theo trong so (cau x pho bien tuyen x pho bien nha xe)
w = (fact_trips.demand_mult * fact_trips.route_pop * fact_trips.popularity).to_numpy()
trip_idx = rng.choice(len(fact_trips), size=N_BOOKINGS_TARGET, p=w / w.sum())
b = fact_trips.loc[trip_idx, ["trip_id", "route_id", "operator_id", "departure_date", "total_seats",
                              "base_fare"]].reset_index(drop=True)
b["seats"] = rng.choice([1, 2, 3, 4], len(b), p=[.70, .20, .07, .03])

# 7b. Ngay dat = ngay khoi hanh - thoi gian dat truoc (dat truoc lau hon vao Tet)
lead = np.minimum(rng.gamma(1.5, 3.0, len(b)), 45)
is_peak = b.departure_date.isin(peak_dates).to_numpy()
lead = np.where(is_peak, lead * 2, lead)
lead = np.minimum(lead, (b.departure_date - pd.Timestamp(START)).dt.days.to_numpy()).astype(int)
b["booking_date"] = b.departure_date - pd.to_timedelta(lead, unit="D")
b["lead_days"] = lead

# 7c. Gioi han suc chua: booking den sau khi chuyen day ghe bi loai (mo phong "het cho")
b["_r"] = rng.random(len(b))
b = b.sort_values(["trip_id", "booking_date", "_r"]).reset_index(drop=True)
b["_cum"] = b.groupby("trip_id").seats.cumsum()
b = b[b._cum <= b.total_seats].drop(columns=["_r", "_cum"]).reset_index(drop=True)

# 7d. Kenh ban
b["channel_id"] = rng.choice(dim_channel.channel_id, len(b), p=CHANNEL_P)

# 7e. Khach hang (phan phoi lech: it khach dat rat nhieu, nhieu khach dat 1 lan)
cust_w = rng.pareto(3.0, N_CUSTOMER_POOL) + 1
b["customer_id"] = rng.choice(np.arange(1, N_CUSTOMER_POOL + 1), len(b), p=cust_w / cust_w.sum())

# 7f. Gia, voucher
b["ticket_price"] = b.base_fare
gross = b.ticket_price * b.seats
b["voucher_id"] = pd.array([pd.NA] * len(b), dtype="Int64")
b["discount_amount"] = 0.0
for _, v in dim_voucher.iterrows():
    active = ((b.booking_date >= v.start_date) & (b.booking_date <= v.end_date)
              & b.voucher_id.isna() & (rng.random(len(b)) < v.use_prob))
    b.loc[active, "voucher_id"] = int(v.voucher_id)
    if v.discount_type == "percent":
        b.loc[active, "discount_amount"] = (gross[active] * v.discount_value).round(-3)
    else:
        b.loc[active, "discount_amount"] = np.minimum(v.discount_value, gross[active] * 0.5)
b["voucher_used"] = b.voucher_id.notna()

# 7g. Trang thai & ngay huy
op_rating = b.operator_id.map(dim_operator.set_index("operator_id").rating)
p_cancel = (0.07
            + np.where(b.route_id == SAPA_ID, 0.11, 0)          # INSIGHT: Ha Noi - Sa Pa huy cao
            + np.where(b.route_id == QUYNHON_ID, 0.04, 0)
            + b.channel_id.map(CHANNEL_CANCEL_EXTRA).to_numpy()
            + np.where(op_rating < 3.8, 0.03, 0))
cancelled = rng.random(len(b)) < p_cancel
refunded = cancelled & (rng.random(len(b)) < 0.30)
b["status"] = np.where(refunded, "Refunded", np.where(cancelled, "Cancelled", "Completed"))
cancel_offset = np.floor(rng.random(len(b)) * (b.lead_days + 1)).astype(int)
b["cancel_date"] = pd.NaT
b.loc[cancelled, "cancel_date"] = (b.booking_date + pd.to_timedelta(cancel_offset, unit="D"))[cancelled]

# 7h. Hoa hong, thu tu booking cua khach (phuc vu retention / khach moi)
b["commission_rate"] = b.operator_id.map(dim_operator.set_index("operator_id").commission_rate)
b = b.sort_values(["booking_date", "trip_id"]).reset_index(drop=True)
b["booking_id"] = np.arange(1, len(b) + 1)
b["booking_seq"] = b.groupby("customer_id").cumcount() + 1
b["is_first_booking"] = b.booking_seq == 1

fact_bookings = b[["booking_id", "booking_date", "departure_date", "trip_id", "route_id", "operator_id",
                   "customer_id", "channel_id", "voucher_id", "voucher_used", "seats", "ticket_price",
                   "discount_amount", "commission_rate", "status", "cancel_date",
                   "lead_days", "booking_seq", "is_first_booking"]]

# =====================================================================
# 8. DIM_CUSTOMER (chi giu khach co phat sinh booking)
# =====================================================================
first_book = fact_bookings.groupby("customer_id").booking_date.min()
dim_customer = first_book.rename("first_booking_date").reset_index()
dim_customer["signup_date"] = dim_customer.first_booking_date - pd.to_timedelta(
    rng.integers(0, 31, len(dim_customer)), unit="D")
dim_customer["province"] = rng.choice(["Hà Nội", "TP.HCM", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Khác"],
                                      len(dim_customer), p=[.28, .32, .08, .06, .05, .21])
dim_customer["age_group"] = rng.choice(["18-24", "25-34", "35-44", "45+"], len(dim_customer),
                                       p=[.30, .38, .20, .12])
dim_customer["device"] = rng.choice(["Android", "iOS", "Desktop"], len(dim_customer), p=[.50, .30, .20])
dim_customer["gender"] = rng.choice(["Nam", "Nữ"], len(dim_customer), p=[.48, .52])

# =====================================================================
# 9. Hoan thien fact_trips (so ghe da ban) + ghi file
# =====================================================================
seat_stats = (fact_bookings.assign(sold=lambda x: np.where(x.status == "Completed", x.seats, 0))
              .groupby("trip_id").agg(seats_booked=("seats", "sum"), seats_sold=("sold", "sum")))
fact_trips = fact_trips.merge(seat_stats, on="trip_id", how="left").fillna({"seats_booked": 0, "seats_sold": 0})
fact_trips[["seats_booked", "seats_sold"]] = fact_trips[["seats_booked", "seats_sold"]].astype(int)
fact_trips["occupancy_rate"] = (fact_trips.seats_sold / fact_trips.total_seats).round(4)
fact_trips = fact_trips[["trip_id", "route_id", "operator_id", "departure_date", "departure_datetime",
                         "total_seats", "base_fare", "seats_booked", "seats_sold", "occupancy_rate"]]

dim_route = dim_route.drop(columns="popularity")
dim_operator = dim_operator.drop(columns="popularity")
dim_voucher = dim_voucher.drop(columns="use_prob")
dim_date = dim_date.drop(columns=["demand_mult", "price_mult"])

tables = {"dim_date": dim_date, "dim_route": dim_route, "dim_operator": dim_operator,
          "dim_customer": dim_customer, "dim_channel": dim_channel, "dim_voucher": dim_voucher,
          "fact_trips": fact_trips, "fact_bookings": fact_bookings}
for name, df in tables.items():
    df.to_csv(os.path.join(OUT_DIR, f"{name}.csv"), index=False, encoding="utf-8-sig")
    print(f"{name:15s} {len(df):>9,d} rows")

# =====================================================================
# 10. Kiem tra nhanh (sanity check)
# =====================================================================
fb = fact_bookings
cancel_rate = fb.status.isin(["Cancelled", "Refunded"]).mean()
print("\n--- SANITY CHECK ---")
print(f"Ty le huy tong: {cancel_rate:.1%}")
print("Ty le huy theo kenh:")
print(fb.assign(c=fb.status != "Completed").merge(dim_channel, on="channel_id")
        .groupby("channel_name").c.mean().round(3).to_string())
print(f"Ty le huy tuyen Sa Pa: {fb[fb.route_id == SAPA_ID].status.ne('Completed').mean():.1%}")
print(f"Ty le lap day ghe TB: {fact_trips.seats_sold.sum() / fact_trips.total_seats.sum():.1%}")
print(f"Ty le dung voucher: {fb.voucher_used.mean():.1%}")
print(f"So khach: {len(dim_customer):,d} | khach quay lai (>=2 booking): "
      f"{(fb.groupby('customer_id').size() > 1).mean():.1%}")
print(f"Khoang ngay booking: {fb.booking_date.min().date()} -> {fb.booking_date.max().date()}")
