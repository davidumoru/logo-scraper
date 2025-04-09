import csv
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
import time
from tqdm import tqdm
import pandas as pd
import concurrent.futures
import random


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)


class LogoScraper:
    def __init__(self, input_file, output_file, max_workers=5, delay=1, timeout=10):
        self.input_file = input_file
        self.output_file = output_file
        self.max_workers = max_workers
        self.delay = delay
        self.timeout = timeout
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
        ]
        
    def read_websites(self):
        try:
            df = pd.read_csv(self.input_file)
            if 'website' not in df.columns:
                logging.error(f"Input file {self.input_file} does not have a 'website' column")
                return []
            
            websites = df['website'].tolist()
            logging.info(f"Loaded {len(websites)} websites from {self.input_file}")
            return websites
        except Exception as e:
            logging.error(f"Error reading input file: {e}")
            return []
    
    def normalize_url(self, url, base_url):
        if not url:
            return None
        
        if url.startswith('//'):
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}:{url}"
        
        if not url.startswith(('http://', 'https://')):
            return urljoin(base_url, url)
        
        return url
    
    def is_likely_logo(self, url, element=None):
        if not url:
            return False
            
        url_lower = url.lower()
        logo_indicators = ['logo', 'brand', 'header', 'site-icon', 'favicon']
        if any(indicator in url_lower for indicator in logo_indicators):
            return True
            
        if url_lower.endswith(('.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp')):
            if element:
                attr_classes = element.get('class', [])
                if isinstance(attr_classes, str):
                    attr_classes = [attr_classes]
                
                attr_id = element.get('id', '')
                
                for indicator in logo_indicators:
                    if (any(indicator in cls.lower() for cls in attr_classes) or 
                        indicator in attr_id.lower()):
                        return True
                        
                alt_text = element.get('alt', '').lower()
                if any(word in alt_text for word in ['logo', 'brand', 'company']):
                    return True
                    
        return False
    
    def find_logo_in_soup(self, soup, base_url):
        logo_candidates = []
        
        for img in soup.find_all('img'):
            src = img.get('src')
            if not src:
                continue
                
            absolute_url = self.normalize_url(src, base_url)
            if self.is_likely_logo(absolute_url, img):
                score = 0
                
                alt_text = img.get('alt', '').lower()
                if 'logo' in alt_text:
                    score += 5
                if any(word in alt_text for word in ['brand', 'company', 'site']):
                    score += 3
                    
                if img.parent and img.parent.name == 'header':
                    score += 3
                if img.parent and img.parent.name == 'a' and img.parent.get('href') == '/':
                    score += 4
                    
                classes = img.get('class', [])
                if isinstance(classes, str):
                    classes = [classes]
                id_attr = img.get('id', '')
                
                if any('logo' in cls.lower() for cls in classes) or 'logo' in id_attr.lower():
                    score += 5
                    
                logo_candidates.append((absolute_url, score))
        
        for svg in soup.find_all('svg'):
            classes = svg.get('class', [])
            if isinstance(classes, str):
                classes = [classes]
            
            if any('logo' in cls.lower() for cls in classes):
                parent = svg.find_parent('a')
                if parent and parent.get('href'):
                    href = self.normalize_url(parent.get('href'), base_url)
                    logo_candidates.append((href, 2))
        
        meta_og_image = soup.find('meta', property='og:image')
        if meta_og_image and meta_og_image.get('content'):
            logo_url = self.normalize_url(meta_og_image.get('content'), base_url)
            logo_candidates.append((logo_url, 3))
            
        for link in soup.find_all('link'):
            rel = link.get('rel', [])
            if isinstance(rel, str):
                rel = [rel]
            
            if any(r in ['icon', 'shortcut icon', 'apple-touch-icon'] for r in rel):
                href = link.get('href')
                if href:
                    logo_url = self.normalize_url(href, base_url)
                    logo_candidates.append((logo_url, 2))
        
        if logo_candidates:
            logo_candidates.sort(key=lambda x: x[1], reverse=True)
            return logo_candidates[0][0]
            
        return None
    
    def scrape_website(self, website):
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
            
        try:
            time.sleep(self.delay * random.uniform(0.5, 1.5))
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(website, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logo_url = self.find_logo_in_soup(soup, website)
            
            if logo_url:
                return website, logo_url, 'success'
            else:
                return website, None, 'no logo found'
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request error for {website}: {e}")
            return website, None, f"request error: {str(e)}"
        except Exception as e:
            logging.error(f"Error processing {website}: {e}")
            return website, None, f"processing error: {str(e)}"
    
    def run(self):
        websites = self.read_websites()
        if not websites:
            logging.error("No websites to process")
            return False
            
        results = []
        
        logging.info(f"Starting scraping {len(websites)} websites with {self.max_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_website = {executor.submit(self.scrape_website, website): website for website in websites}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_website), total=len(websites)):
                website = future_to_website[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logging.error(f"Unhandled exception for {website}: {e}")
                    results.append((website, None, f"unhandled error: {str(e)}"))
        
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['website', 'logo_url', 'status'])
                writer.writerows(results)
                
            logging.info(f"Results saved to {self.output_file}")
            
            success_count = sum(1 for _, logo_url, _ in results if logo_url is not None)
            logging.info(f"Extracted {success_count} logos out of {len(websites)} websites " +
                        f"({success_count / len(websites) * 100:.1f}% success rate)")
                        
            return True
        except Exception as e:
            logging.error(f"Error saving results: {e}")
            return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape logos from websites")
    parser.add_argument("--input", "-i", default="websites.csv", help="Input CSV file with websites")
    parser.add_argument("--output", "-o", default="logos.csv", help="Output CSV file for logo URLs")
    parser.add_argument("--workers", "-w", type=int, default=5, help="Number of worker threads")
    parser.add_argument("--delay", "-d", type=float, default=1.0, help="Delay between requests in seconds")
    parser.add_argument("--timeout", "-t", type=int, default=10, help="Request timeout in seconds")
    
    args = parser.parse_args()
    
    scraper = LogoScraper(
        input_file=args.input,
        output_file=args.output,
        max_workers=args.workers,
        delay=args.delay,
        timeout=args.timeout
    )
    
    scraper.run()