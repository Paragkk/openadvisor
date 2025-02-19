import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Set the path to the instance folder
instance_folder = os.path.join(current_directory, 'instance')

# Construct the absolute path to the database file within the instance folder
db_file_path = os.path.join(instance_folder, os.getenv('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', ''))

# Ensure the predictions folder exists
predictions_folder = os.getenv('PREDICTIONS_FOLDER', 'predictions')
os.makedirs(predictions_folder, exist_ok=True)

# Load the existing aggregate predictions
aggregate_predictions_path = os.path.join(predictions_folder, 'aggregate_30day_predictions.csv')
aggregate_df = pd.read_csv(aggregate_predictions_path)

# Function to get the lowest and highest prices in the last one month
def get_last_month_prices(symbol):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    data = yf.download(symbol, start=start_date, end=end_date)
    if not data.empty:
        lowest_price = data['Low'].min().item()
        print(lowest_price)
        highest_price = data['High'].max().item()
        return lowest_price, highest_price
    return None, None

# Add new columns to the aggregate DataFrame
aggregate_df['Lowest Price Last Month'] = None
aggregate_df['Highest Price Last Month'] = None
aggregate_df['Predicted Close in Range'] = None

# Update the DataFrame with the new data
for index, row in aggregate_df.iterrows():
    symbol = row['Stock']
    lowest_price, highest_price = get_last_month_prices(symbol)
    if lowest_price is not None and highest_price is not None:
        aggregate_df.at[index, 'Lowest Price Last Month'] = lowest_price
        aggregate_df.at[index, 'Highest Price Last Month'] = highest_price
        
        # Ensure predicted_close is a scalar value
        predicted_close = row['30 day Closing']
        if isinstance(predicted_close, pd.Series):
            predicted_close = predicted_close.item()  # Convert Series to scalar
        elif isinstance(predicted_close, str):
            # Handle case where predicted_close is a string (e.g., "1.23")
            try:
                predicted_close = float(predicted_close)
            except ValueError:
                print(f"Invalid value for '30 day Closing' in row {index}: {predicted_close}")
                predicted_close = None
        
        # Perform the comparison only if predicted_close is a valid scalar
        if predicted_close is not None:
            print(f"Predicted close for {symbol}: {predicted_close}")
            
            print(f"Highest price in last month: {highest_price}")
            aggregate_df.at[index, 'Predicted Close in Range'] = (lowest_price <= predicted_close <= highest_price)

# Save the updated DataFrame to the CSV file
aggregate_df.to_csv(aggregate_predictions_path, index=False)
print(f"Updated aggregate results saved to '{aggregate_predictions_path}'")

# Optional: Print the updated DataFrame to confirm
print(aggregate_df)