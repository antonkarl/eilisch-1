from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)
# Replace 'your-api-key' with your actual OpenAI API key

def get_word_splits(word_list):
    # Define the prompt with your words
    prompt = "Split the following Icelandic words that are made up of two or more words. Use a hyphen '-' between each split. Do not add any explanation or numbering. Just output the splits in a new line for each word:\n\n"
    prompt += '\n'.join(word_list)
    
    # Make the API call
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the text response
    return completion.choices[0].message.content.strip().split()

# Your list of Icelandic words
word_list = [
    "heilmikil", "nýtast", "út", "útgáfu", "viðbót", "aukalögþingunum",
    "getur", "út", "bak", "allmikið", "rit", "líka", "auk", "búskaparhætti",
    "leita", "handritasafni", "Landsbókasafns", "Háskólabókasafns", "forseti",
    "tókst", "flutning", "mikla", "baki", "beiti", "lokinni", "nákvæmlega", 
    "hljóta", "breytingu", "svipaðan"
]

# Call the function and print the result
word_splits = get_word_splits(word_list)
print(word_splits)
