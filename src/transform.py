from .extract import COL_DISTANCE, COL_AVG_SPEED, COL_MAX_SPEED, FUEL_EFFICIENCY_KM_PER_LITER, FUEL_PRICE_PER_LITER


def convert_to_01(df, col):
    """Convert 'yes'/'no' to 1/0 in specified column."""
    # check if column have int values, if not convert to 01
    if df[col].dtype in (int, float):
        return df
    else:   
        df[col] = df[col].str.strip().str.lower().map({"yes": 1, "no": 0})
        return df


def build_summary(df):
    """Group by unit, calculate KPIs: distance, speed, fuel, cost, off-hours, night metrics."""
    df = convert_to_01(df, "off_hours")

    summary = df.groupby("unit").agg(
        distance_km = (COL_DISTANCE,  "sum"),
        avg_speed_kmh = (COL_AVG_SPEED, "mean"),
        max_speed_kmh = (COL_MAX_SPEED, "max"),
        off_hours_trips = ("off_hours", "sum"),
        total_trips = ("unit", "count"),
        distance_avg_per_trip = (COL_DISTANCE, "mean"),
    )

    # Fuel metrics
    summary["liters"] = summary["distance_km"] / FUEL_EFFICIENCY_KM_PER_LITER
    summary["cost"] = summary["liters"] * FUEL_PRICE_PER_LITER
    summary["agency"] = df.groupby("unit")["agency"].first() # get agency name for each unit (assuming it's consistent per unit)

    # fit position of agent column to first column
    agency = summary.pop("agency") # remove agency if exists, otherwise return None
    summary.insert(0, "agency", agency) # insert agency back to first column 

    # Night metrics
    df_night = df[df["off_hours"] == 1]
    night = df_night.groupby("unit")[COL_DISTANCE].sum().rename("distance_night")
    summary = summary.join(night)
    summary["cost_night"] = (summary["distance_night"] / FUEL_EFFICIENCY_KM_PER_LITER) * FUEL_PRICE_PER_LITER

    # Traffic light
    def traffic_light(km):
        if km < 3000:    return "green"
        elif km <= 6000: return "yellow"
        else:            return "red"

    summary["status"] = summary["distance_km"].apply(traffic_light)

    return summary.sort_values("cost", ascending=False)
