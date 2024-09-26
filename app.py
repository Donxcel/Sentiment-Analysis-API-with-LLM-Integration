from flask import Flask, request, jsonify
import pandas as pd
import os
import groq  # Import Groq library
from groq import Groq,Client  # Import Groq library
from dotenv import load_dotenv, find_dotenv
import json  # Import json library


app = Flask(__name__)

#this function is to get the sentiment analysis from the API we are using
def analyze_sentiment(review_text):
    try:
        client = Groq(
        # This is the default and can be omitted
        api_key=os.environ.get("NEW_GROQ_API_KEY"),
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"perform sentiment analysis on the input text: {review_text} I should just see number the number count of positive, negative, and neutral sentiments as output i.e postive:2 negative:0, neutral:0 the n u strip any text after that",
                } 
            ],
            model="llama3-8b-8192",
        )
        ### Here I am cleaning the data to ease the sentiment analysis and to get the number of positive, negative, and neutral sentiments
        collected_response = str(chat_completion.choices[0].message.content).lower()
        collected_response = collected_response[collected_response.find('positive:'):collected_response.find('neutral:')+10]
        store = {} ### we use a dict n loop to extract the various numbers from the response
        length = ''
        for i in collected_response:
            try:
                int(i)  # Try to convert the character to an integer
                length += str(i)
                if len(length) == 1: store['positive'] = i# Append the integer to the list
                if len(length) == 2: store['negative'] = i# Append the integer to the list
                if len(length) == 3: store['neutral'] = i# Append the integer to the list
            except ValueError:
                pass
        return store  # Expected to return {'positive': x, 'negative': y, 'neutral': z}
    
    except groq.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
    except groq.RateLimitError as e:
        print("A 429 status code was received; we should back off a bit.")
    except groq.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)

'''Now we start creating our API endpoints for the web application'''

# Set the maximum size for file uploads if needed (optional)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Route to upload files
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        file_path = os.path.join('/tmp', file.filename)
        file.save(file_path)
        print('all good')
        try:
            reviews = extract_reviews(file_path)
            positive, negative, neutral = 0, 0, 0

            # Perform sentiment analysis for each review
            for review in reviews:
                try:
                    sentiment = analyze_sentiment(review)
                    positive += int(sentiment['positive']) # Add the positive sentiment score to the total
                    negative += int(sentiment['negative']) # Add the negative sentiment score to the total
                    neutral += int(sentiment['neutral']) # Add the neutral sentiment score to the total
                except Exception as e:
                    print(e)
            # Calculate the average sentiment scores
            positive = positive / (positive+negative+neutral) * 100
            negative = negative / (positive+negative+neutral) * 100
            neutral = neutral / (positive+negative+neutral) * 100

            # Return the sentiment scores in percentages
            return jsonify({
                "positive": round(positive, 2),  # Round to 2 decimal places
                "negative": round(negative, 2),  # Round to 2 decimal placesi wan deploy that njang
                "neutral": round(neutral, 2)     # Round to 2 decimal places
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid file format, only CSV and XLSX are allowed"}), 400
    


# Function to extract reviews from CSV or XLSX
def extract_reviews(file_path):
    # Load the file using pandas
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path)
    
    # Assuming the reviews are stored in a column named 'review' (adjust as needed)
    if 'Review' not in df.columns:
        raise ValueError("File does not contain 'review' column")
    
    # Return the list of reviews
    return df['Review'].tolist()




# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)
