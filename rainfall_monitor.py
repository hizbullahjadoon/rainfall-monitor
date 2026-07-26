import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import time

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_DIR = "rainfall_output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

STATIONS = {
    "River Indus": [
        ("Kargil", 34.56, 76.13),
        ("Leh and Ladakh", 34.15, 77.58),
        ("Kakul", 34.18, 73.25),
        ("Malam Jabba", 34.79, 72.57),
    ],
    "River Jhelum": [
        ("Srinagar", 34.08, 74.79),
        ("Bandipore", 34.42, 74.64),
        ("Pulwama", 33.87, 74.89),
        ("Badgam", 34.02, 74.77),
        ("Kupwara", 34.53, 74.26),
        ("Baramulla", 34.20, 74.35),
        ("Anantnag", 33.73, 75.15),
        ("Poonch", 33.77, 74.09),
        ("Qila Rohtas", 32.65, 73.58),
        ("Mangla", 33.14, 73.64),
        ("Mandi Bahauddin", 32.59, 73.49),
        ("Chakwal", 32.93, 72.86),
        ("Palandri", 33.71, 73.75),
    ],
    "River Chenab": [
        ("Kishtwar", 33.31, 75.77),
        ("Ramban", 33.24, 75.24),
        ("Reasi", 33.08, 74.83),
        ("Jammu", 32.73, 74.86),
        ("Rajouri", 33.38, 74.31),
        ("Doda", 33.15, 75.55),
        ("Gujranwala", 32.16, 74.19),
        ("Sialkot", 32.49, 74.52),
        ("Hafizabad", 32.07, 73.69),
        ("Gujrat", 32.57, 74.08),
    ],
    "River Ravi": [
        ("Chamba", 32.55, 76.13),
        ("Kathua", 32.37, 75.52),
        ("Gurdaspur", 32.04, 75.40),
        ("Pathankot", 32.27, 75.65),
        ("Narowal", 32.10, 74.87),
        ("Okara", 30.81, 73.45),
        ("Lahore", 31.52, 74.36),
    ],
    "River Sutlej": [
        ("Bilaspur", 31.33, 76.76),
        ("Kangra", 32.10, 76.27),
        ("Kullu", 31.96, 77.11),
        ("Mandi", 31.71, 76.93),
        ("Solan", 30.90, 77.10),
        ("Hoshiarpur", 31.53, 75.91),
        ("Kapurthala", 31.38, 75.38),
        ("Bahawalnagar", 29.99, 73.25),
    ],
    "Nullah Aik & Palku": [
        ("Udhampur", 32.92, 75.14),
    ],
    "Nullah Deg": [
        ("Samba", 32.57, 75.12),
    ]
}


def get_location_rainfall(latitude, longitude, target_date):
    start_date = target_date
    end_date = target_date + timedelta(days=1)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "precipitation",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "timezone": "Asia/Karachi",
        "cell_selection": "land"
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        hourly = data.get("hourly", {})

        times = hourly.get("time", [])
        precipitation = hourly.get("precipitation", [])

        if not times:
            return np.nan

        df = pd.DataFrame({
            "time": times,
            "precipitation": precipitation
        })

        df["time"] = pd.to_datetime(df["time"])

        df = df[
            df["time"].dt.date == target_date
        ]

        rainfall = df["precipitation"].sum()

        return round(float(rainfall), 1)

    except Exception as e:
        print(
            f"Error for {latitude}, {longitude}: {e}"
        )
        return np.nan


def collect_rainfall_data():
    from zoneinfo import ZoneInfo
    
    today = datetime.now(
        ZoneInfo("Asia/Karachi")
    ).date()

    yesterday = today - timedelta(days=1)

    print(f"Current date: {today}")
    print(f"Previous date: {yesterday}")

    records = []

    for river, stations in STATIONS.items():

        print(f"Processing: {river}")

        for station_name, lat, lon in stations:

            print(f"  {station_name}")

            rainfall_yesterday = get_location_rainfall(
                lat,
                lon,
                yesterday
            )

            rainfall_today = get_location_rainfall(
                lat,
                lon,
                today
            )

            records.append({
                "River": river,
                "Station": station_name,
                "Latitude": lat,
                "Longitude": lon,
                str(yesterday): rainfall_yesterday,
                str(today): rainfall_today
            })

    df = pd.DataFrame(records)

    return df, yesterday, today


def save_data(df, yesterday, today):
    date_string = today.strftime("%Y-%m-%d")

    csv_file = os.path.join(
        OUTPUT_DIR,
        f"rainfall_{date_string}.csv"
    )

    excel_file = os.path.join(
        OUTPUT_DIR,
        f"rainfall_{date_string}.xlsx"
    )

    df.to_csv(
        csv_file,
        index=False
    )

    df.to_excel(
        excel_file,
        index=False
    )

    print(f"\nCSV saved: {csv_file}")
    print(f"Excel saved: {excel_file}")


def create_html_table(df, yesterday, today):
    yesterday_str = str(yesterday)
    today_str = str(today)

    html_file = os.path.join(
        OUTPUT_DIR,
        f"rainfall_table_{today}.html"
    )

    all_values = pd.concat([
        df[yesterday_str],
        df[today_str]
    ]).dropna()

    max_rainfall = (
        all_values.max()
        if len(all_values) > 0
        else 1
    )

    def rainfall_cell(value):
        if pd.isna(value):
            return """
            <td class="rainfall">
                <span>-</span>
            </td>
            """

        width = (
            value / max_rainfall
        ) * 100

        return f"""
        <td class="rainfall">
            <div class="bar-container">
                <div class="rain-bar"
                     style="width: {width:.2f}%;">
                </div>
                <span class="rain-value">
                    {value:.1f}
                </span>
            </div>
        </td>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<title>
Complete Upper Indus Basin Catchments
</title>

<style>

body {{
    font-family: Arial, sans-serif;
    background: #f5f5f5;
    padding: 30px;
}}

.container {{
    max-width: 850px;
    margin: auto;
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}}

h1 {{
    text-align: center;
    color: #1e3a8a;
    margin-bottom: 5px;
}}

.subtitle {{
    text-align: center;
    font-size: 16px;
    margin-bottom: 20px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th,
td {{
    border: 1px solid #cccccc;
    padding: 7px;
    text-align: center;
}}

th {{
    background: #e5e7eb;
    font-weight: bold;
}}

.station {{
    text-align: left;
    width: 40%;
}}

.river {{
    font-size: 18px;
    font-weight: bold;
    color: #1e3a8a;
    background: #dbeafe;
    text-align: center;
}}

.rainfall {{
    width: 30%;
}}

.bar-container {{
    position: relative;
    height: 24px;
    width: 100%;
    background: #f1f5f9;
    overflow: hidden;
}}

.rain-bar {{
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    background: #86efac;
    opacity: 0.75;
}}

.rain-value {{
    position: relative;
    z-index: 2;
    font-weight: bold;
    line-height: 24px;
}}

</style>
</head>

<body>

<div class="container">

<h1>
Complete Upper Indus Basin Catchments
</h1>

<div class="subtitle">
Last 24 Hour Rainfall (mm)
</div>

<table>

<tr>
<th>Location</th>
<th>{yesterday_str}</th>
<th>{today_str}</th>
</tr>
"""

    for river in STATIONS.keys():

        html += f"""
<tr>
<td colspan="3" class="river">
{river}
</td>
</tr>
"""

        river_df = df[
            df["River"] == river
        ]

        for _, row in river_df.iterrows():

            old_cell = rainfall_cell(
                row[yesterday_str]
            )

            new_cell = rainfall_cell(
                row[today_str]
            )

            html += f"""
<tr>

<td class="station">
{row["Station"]}
</td>

{old_cell}

{new_cell}

</tr>
"""

    html += """
</table>

</div>

</body>
</html>
"""

    with open(
        html_file,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(html)

    print(
        f"HTML table saved: {html_file}"
    )

def create_png_table(df, yesterday, today):
    yesterday_str = str(yesterday)
    today_str = str(today)

    all_values = pd.concat([
        df[yesterday_str],
        df[today_str]
    ]).dropna()

    max_rainfall = (
        all_values.max()
        if len(all_values) > 0
        else 1
    )

    # Prevent zero division
    if max_rainfall == 0:
        max_rainfall = 1

    rows = []
    river_rows = []

    # Header row
    rows.append([
        "Location",
        yesterday_str,
        today_str
    ])

    # Build table rows
    for river in STATIONS.keys():

        # Store the row number of the river header
        river_rows.append(len(rows))

        rows.append([
            river,
            "",
            ""
        ])

        river_df = df[
            df["River"] == river
        ]

        for _, row in river_df.iterrows():

            old_value = row[yesterday_str]
            new_value = row[today_str]

            old_display = (
                "-"
                if pd.isna(old_value)
                else f"{old_value:.1f}"
            )

            new_display = (
                "-"
                if pd.isna(new_value)
                else f"{new_value:.1f}"
            )

            rows.append([
                row["Station"],
                old_display,
                new_display
            ])

    # Figure size
    fig_height = (
        len(rows) * 0.45 + 2
    )

    fig, ax = plt.subplots(
        figsize=(10, fig_height)
    )

    ax.axis("off")

    # Create table
    table = ax.table(
        cellText=rows[1:],
        colLabels=rows[0],
        cellLoc="center",
        colLoc="center",
        bbox=[
            0,
            0,
            1,
            0.94
        ],
        colWidths=[
            0.45,
            0.275,
            0.275
        ]
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Force drawing of table so cell positions are available
    fig.canvas.draw()

    # Header styling
    for col in range(3):

        cell = table[0, col]

        cell.set_text_props(
            weight="bold"
        )

        cell.set_facecolor(
            "#e5e7eb"
        )

    # River header styling
    for row_index in river_rows:

        for col in range(3):

            cell = table[
                row_index,
                col
            ]

            cell.set_text_props(
                weight="bold"
            )

            cell.set_facecolor(
                "#dbeafe"
            )

    # Add rainfall bars
    for row_index in range(
        1,
        len(rows)
    ):

        # Skip river header rows
        if row_index in river_rows:
            continue

        # --------------------------------------------------
        # Previous date
        # --------------------------------------------------

        for col_index, value in [
            (1, rows[row_index][1]),
            (2, rows[row_index][2])
        ]:

            if value == "-":
                continue

            try:
                rainfall = float(value)
            except:
                continue

            # Get table cell
            cell = table[
                row_index,
                col_index
            ]

            # Cell coordinates in axes coordinates
            x = cell.get_x()
            y = cell.get_y()

            width = cell.get_width()
            height = cell.get_height()

            # Percentage of maximum rainfall
            bar_percentage = (
                rainfall / max_rainfall
            )

            # Limit between 0 and 1
            bar_percentage = max(
                0,
                min(
                    bar_percentage,
                    1
                )
            )

            # Bar width
            bar_width = (
                width
                * bar_percentage
            )

            # Draw bar
            rectangle = plt.Rectangle(
                (
                    x,
                    y
                ),
                bar_width,
                height,
                transform=ax.transAxes,
                facecolor="#86efac",
                alpha=0.65,
                zorder=10
            )

            ax.add_patch(
                rectangle
            )

            # Move text above bar
            cell.get_text().set_zorder(
                20
            )

            cell.get_text().set_fontweight(
                "bold"
            )

    # Title
    plt.title(
        "Complete Upper Indus Basin Catchments",
        fontsize=18,
        fontweight="bold",
        pad=20
    )

    # Subtitle
    fig.text(
        0.5,
        0.955,
        f"Last 24 Hour Rainfall (mm) | "
        f"{today.strftime('%d/%m/%Y')}",
        ha="center",
        fontsize=12
    )

    # Output path
    png_file = os.path.join(
        OUTPUT_DIR,
        f"rainfall_table_{today}.png"
    )

    # Save
    plt.savefig(
        png_file,
        dpi=200,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.close()

    print(
        f"PNG table saved: {png_file}"
    )

def main():
    print("UPPER INDUS BASIN")
    print("24-HOUR RAINFALL MONITOR")

    df, yesterday, today = (
        collect_rainfall_data()
    )

    print("\nFINAL DATA")
    print(df.to_string(index=False))

    save_data(
        df,
        yesterday,
        today
    )

    create_html_table(
        df,
        yesterday,
        today
    )

    create_png_table(
        df,
        yesterday,
        today
    )

    print("\nPROCESS COMPLETED")


if __name__ == "__main__":
    main()