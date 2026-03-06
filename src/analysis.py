from .ingestion import COL_DISTANCE, COL_AVG_SPEED, COL_MAX_SPEED, FUEL_EFFICIENCY_KM_PER_LITER, FUEL_PRICE_PER_LITER


def build_summary(df):
    """Group by unit, calculate KPIs: distance, speed, fuel, cost, off-hours, night metrics."""
    summary = df.groupby("unit").agg(
        distance_km   =(COL_DISTANCE,  "sum"),
        avg_speed_kmh =(COL_AVG_SPEED, "mean"),
        max_speed_kmh =(COL_MAX_SPEED, "max"),
        off_hours_trips=("off_hours",  "sum"),
    )

    summary["liters"] = summary["distance_km"] / FUEL_EFFICIENCY_KM_PER_LITER
    summary["cost"]   = summary["liters"] * FUEL_PRICE_PER_LITER

    # Night metrics
    df_night = df[df["off_hours"] == "yes"]
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
