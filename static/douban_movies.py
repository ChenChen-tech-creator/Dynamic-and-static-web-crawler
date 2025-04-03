import requests
from bs4 import BeautifulSoup
import time
import csv
import random
from typing import List, Tuple

def get_headers() -> dict:
    """Return headers to mimic a real browser."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def get_movie_data(url: str) -> List[Tuple[str, float]]:
    """Fetch and parse movie data from the given URL."""
    movies = []
    
    try:
        # Add a random delay between requests (1-3 seconds)
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()  # Raise an exception for bad status codes
        
        soup = BeautifulSoup(response.text, 'html.parser')
        movie_items = soup.find_all('div', class_='item')
        
        for item in movie_items:
            # Extract movie title
            title = item.find('span', class_='title').text.strip()
            
            # Extract rating
            rating = float(item.find('span', class_='rating_num').text.strip())
            
            movies.append((title, rating))
            
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
    except Exception as e:
        print(f"Error parsing data: {e}")
        
    return movies

def save_to_csv(movies: List[Tuple[str, float]], filename: str = 'douban_top250.csv'):
    """Save movie data to a CSV file."""
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Movie Title', 'Rating'])
            writer.writerows(movies)
        print(f"Data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def main():
    base_url = 'https://movie.douban.com/top250'
    all_movies = []
    
    # Fetch all 10 pages
    for page in range(10):
        url = f"{base_url}?start={page * 25}"
        print(f"Fetching page {page + 1}...")
        
        movies = get_movie_data(url)
        all_movies.extend(movies)
        
        # Add a longer delay between pages (2-4 seconds)
        time.sleep(random.uniform(2, 4))
    
    # Save all movies to CSV
    save_to_csv(all_movies)
    print(f"Total movies scraped: {len(all_movies)}")

if __name__ == "__main__":
    main() 