import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import re
import os
from scipy.spatial.distance import cosine
import difflib
import math
from datetime import datetime
import requests

# Set page config
st.set_page_config(
    page_title="RankBuddy - SEO Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class KeywordAPI:
    """Free API integration for real keyword data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_google_suggestions(self, keyword):
        """Get Google autocomplete suggestions for keyword"""
        try:
            url = "http://suggestqueries.google.com/complete/search"
            params = {
                'client': 'firefox',
                'q': keyword,
                'hl': 'en'
            }
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and isinstance(data[1], list):
                    return [suggestion for suggestion in data[1] if suggestion and len(suggestion) > 2]
            return []
        except Exception as e:
            st.warning(f"Google Suggestions API error: {str(e)}")
            return []
    
    def get_related_keywords_from_datamuse(self, keyword):
        """Get related keywords from Datamuse API (free)"""
        try:
            # Get words with similar meaning
            url = "https://api.datamuse.com/words"
            params = {
                'ml': keyword,  # similar meaning
                'max': 20
            }
            response = self.session.get(url, params=params, timeout=10)
            related_words = []
            
            if response.status_code == 200:
                data = response.json()
                related_words.extend([item['word'] for item in data])
            
            # Get words that often appear with this word
            params = {
                'rel_trg': keyword,  # words that often follow
                'max': 15
            }
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                related_words.extend([item['word'] for item in data])
            
            return list(set(related_words))[:25]  # Remove duplicates and limit
            
        except Exception as e:
            st.warning(f"Datamuse API error: {str(e)}")
            return []
    
    def get_wiki_related_terms(self, keyword):
        """Get related terms from Wikipedia API (free)"""
        try:
            # Search Wikipedia for the keyword
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + keyword.replace(' ', '_')
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                extract = data.get('extract', '')
                
                # Extract important terms from the summary
                words = re.findall(r'\b[A-Za-z]{4,}\b', extract.lower())
                # Filter out common words and return unique terms
                stopwords = {'that', 'with', 'have', 'this', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'also', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'than', 'only', 'come', 'year', 'work', 'such', 'make', 'them', 'well', 'were'}
                filtered_words = [word for word in set(words) if len(word) > 4 and word not in stopwords]
                return filtered_words[:15]
            
            return []
            
        except Exception as e:
            st.warning(f"Wikipedia API error: {str(e)}")
            return []
    
    def estimate_real_difficulty(self, keyword):
        """Estimate difficulty based on real search data"""
        try:
            # Use Google search to estimate competition
            url = "https://www.google.com/search"
            params = {
                'q': f'"{keyword}"',  # Exact phrase search
                'num': 1
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Extract approximate result count from the page
                content = response.text
                # Look for result count patterns
                import re
                result_patterns = [
                    r'About ([\d,]+) results',
                    r'([\d,]+) results',
                    r'Approximately ([\d,]+) results'
                ]
                
                for pattern in result_patterns:
                    match = re.search(pattern, content)
                    if match:
                        result_count = int(match.group(1).replace(',', ''))
                        # Convert to difficulty score (0-100)
                        if result_count < 10000:
                            return min(20, max(5, result_count / 500))  # Very easy
                        elif result_count < 100000:
                            return min(40, max(20, result_count / 2500))  # Easy
                        elif result_count < 1000000:
                            return min(60, max(40, result_count / 16667))  # Medium
                        elif result_count < 10000000:
                            return min(80, max(60, result_count / 125000))  # Hard
                        else:
                            return min(95, max(80, result_count / 1000000))  # Very hard
            
            # Fallback to heuristic scoring
            words = keyword.lower().split()
            word_count = len(words)
            avg_length = sum(len(word) for word in words) / len(words) if words else 0
            
            # Base difficulty on length and word count
            base_score = max(0, 50 - (word_count * 8) - (avg_length * 2))
            return min(100, max(10, base_score))
            
        except Exception as e:
            # Fallback to simple heuristic
            words = keyword.lower().split()
            word_count = len(words)
            avg_length = sum(len(word) for word in words) / len(words) if words else 0
            base_score = max(0, 50 - (word_count * 8) - (avg_length * 2))
            return min(100, max(10, base_score))

class SEOAnalyzer:
    def __init__(self):
        self.common_words = self.load_common_words()
        self.stopwords = self.load_stopwords()
        self.word_frequencies = self.load_word_frequencies()
        self.api = KeywordAPI()
        
    def load_common_words(self):
        """Load common English words for keyword generation"""
        # Common English words that are often used in blog posts
        return {
            'how', 'what', 'why', 'when', 'where', 'guide', 'tutorial', 'tips',
            'best', 'top', 'review', 'comparison', 'vs', 'versus', 'ultimate',
            'complete', 'beginner', 'advanced', 'step', 'steps', 'easy', 'simple',
            'quick', 'fast', 'effective', 'proven', 'examples', 'case', 'study',
            'free', 'tools', 'software', 'app', 'platform', 'service', 'solution',
            'strategy', 'method', 'technique', 'approach', 'way', 'ways', 'ideas',
            'checklist', 'framework', 'process', 'system', 'hack', 'hacks',
            'secret', 'secrets', 'trick', 'tricks', 'mistake', 'mistakes',
            'common', 'popular', 'trending', 'latest', 'new', 'updated', 'modern',
            'business', 'marketing', 'growth', 'success', 'profitable', 'money',
            'startup', 'entrepreneur', 'founder', 'indie', 'solo', 'small',
            'online', 'digital', 'internet', 'web', 'website', 'blog', 'content',
            'seo', 'optimization', 'rank', 'ranking', 'google', 'search', 'traffic'
        }
    
    def load_stopwords(self):
        """Load stopwords to filter out"""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'or', 'but', 'if', 'then', 'than',
            'this', 'these', 'they', 'them', 'their', 'there', 'we', 'you',
            'your', 'i', 'me', 'my', 'mine', 'our', 'ours', 'us'
        }
    
    def load_word_frequencies(self):
        """Load word frequency data for difficulty estimation"""
        # Simulated frequency data based on common patterns
        base_freq = {
            'how': 850000, 'what': 750000, 'best': 680000, 'top': 620000,
            'guide': 450000, 'tips': 380000, 'review': 320000, 'free': 280000,
            'tutorial': 240000, 'business': 220000, 'marketing': 180000,
            'seo': 160000, 'growth': 140000, 'startup': 120000, 'tools': 110000,
            'strategy': 95000, 'success': 85000, 'online': 75000, 'digital': 65000,
            'beginner': 55000, 'advanced': 45000, 'complete': 40000, 'ultimate': 35000,
            'simple': 30000, 'easy': 28000, 'quick': 25000, 'step': 22000,
            'effective': 20000, 'proven': 18000, 'examples': 16000, 'case': 15000,
            'study': 14000, 'method': 13000, 'technique': 12000, 'approach': 11000,
            'framework': 10000, 'process': 9500, 'system': 9000, 'hack': 8500,
            'secret': 8000, 'trick': 7500, 'mistake': 7000, 'common': 6500,
            'popular': 6000, 'trending': 5500, 'latest': 5000, 'new': 4800,
            'updated': 4600, 'modern': 4400, 'profitable': 4200, 'money': 4000,
            'entrepreneur': 3800, 'founder': 3600, 'indie': 3400, 'solo': 3200,
            'small': 3000, 'website': 2800, 'blog': 2600, 'content': 2400,
            'optimization': 2200, 'rank': 2000, 'ranking': 1800, 'google': 1600,
            'search': 1400, 'traffic': 1200, 'conversion': 1000, 'funnel': 900,
            'leads': 800, 'sales': 700, 'revenue': 600, 'profit': 500
        }
        return base_freq
    
    def generate_related_keywords(self, seed_keyword, max_keywords=20, use_api=True):
        """Generate related keywords using both offline analysis and real API data"""
        seed_words = self.clean_text(seed_keyword).split()
        related_keywords = set()
        
        # Add seed keyword
        related_keywords.add(seed_keyword.lower())
        
        # Get real data from APIs if enabled
        if use_api:
            try:
                # Get Google autocomplete suggestions
                google_suggestions = self.api.get_google_suggestions(seed_keyword)
                related_keywords.update(google_suggestions)
                
                # Get related words from Datamuse API
                datamuse_words = self.api.get_related_keywords_from_datamuse(seed_keyword)
                for word in datamuse_words:
                    related_keywords.add(f"{word} {seed_keyword}")
                    related_keywords.add(f"{seed_keyword} {word}")
                    related_keywords.add(word)
                
                # Get Wikipedia related terms
                wiki_terms = self.api.get_wiki_related_terms(seed_keyword)
                for term in wiki_terms:
                    related_keywords.add(f"{term} {seed_keyword}")
                    related_keywords.add(f"{seed_keyword} {term}")
                
            except Exception as e:
                st.warning(f"API fetch error, using offline data: {str(e)}")
        
        # Generate combinations with common SEO words (offline backup)
        for word in seed_words:
            for common_word in self.common_words:
                # Prefix combinations
                related_keywords.add(f"{common_word} {word}")
                related_keywords.add(f"{common_word} {seed_keyword}")
                # Suffix combinations
                related_keywords.add(f"{word} {common_word}")
                related_keywords.add(f"{seed_keyword} {common_word}")
        
        # Generate long-tail variations
        long_tail_modifiers = [
            "for beginners", "step by step", "in 2024", "complete guide",
            "best practices", "case study", "examples", "tutorial",
            "how to", "why you need", "mistakes to avoid", "tips and tricks",
            "free", "online", "software", "tools", "strategy", "tips"
        ]
        
        for modifier in long_tail_modifiers:
            related_keywords.add(f"{seed_keyword} {modifier}")
            related_keywords.add(f"{modifier} {seed_keyword}")
        
        # Filter and sort by relevance
        filtered_keywords = []
        for keyword in related_keywords:
            if len(keyword.split()) <= 6 and len(keyword) >= 3:
                similarity = self.calculate_similarity(seed_keyword, keyword)
                filtered_keywords.append((keyword, similarity))
        
        # Sort by similarity and return top keywords
        filtered_keywords.sort(key=lambda x: x[1], reverse=True)
        return [kw[0] for kw in filtered_keywords[:max_keywords * 2]]  # Return more keywords since we have better data
    
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two text strings"""
        return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def clean_text(self, text):
        """Clean text for analysis"""
        # Remove special characters and convert to lowercase
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
        return text
    
    def estimate_keyword_difficulty(self, keyword):
        """Estimate keyword difficulty using heuristics"""
        words = self.clean_text(keyword).split()
        
        # Factors affecting difficulty
        word_count = len(words)
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Check word frequency
        total_frequency = 0
        for word in words:
            if word in self.word_frequencies:
                total_frequency += self.word_frequencies[word]
        
        # Calculate difficulty score (0-100)
        # Higher frequency = higher difficulty
        frequency_score = min(total_frequency / 10000, 50)  # Cap at 50
        
        # Longer phrases are generally easier
        length_score = max(0, 30 - (word_count * 5))
        
        # Longer words are generally more specific (easier)
        word_length_score = max(0, 20 - (avg_word_length * 2))
        
        difficulty = frequency_score + length_score + word_length_score
        return min(max(difficulty, 0), 100)  # Clamp between 0-100
    
    def suggest_blog_structure(self, keyword, related_keywords):
        """Suggest blog post structure based on keyword analysis"""
        structure = {
            'title_suggestions': [],
            'headings': [],
            'meta_description': '',
            'keyword_density': 0.015,  # 1.5%
            'word_count_target': 1500
        }
        
        # Title suggestions
        title_templates = [
            f"The Ultimate Guide to {keyword.title()}",
            f"How to {keyword.title()}: Complete Tutorial",
            f"{keyword.title()}: Best Practices and Tips",
            f"Everything You Need to Know About {keyword.title()}",
            f"{keyword.title()} for Beginners: Step-by-Step Guide"
        ]
        structure['title_suggestions'] = title_templates
        
        # Heading structure
        headings = [
            f"What is {keyword.title()}?",
            f"Why {keyword.title()} Matters",
            f"How to Get Started with {keyword.title()}",
            f"Best Practices for {keyword.title()}",
            f"Common Mistakes to Avoid",
            f"Tools and Resources",
            f"Case Studies and Examples",
            f"Conclusion"
        ]
        structure['headings'] = headings
        
        # Meta description
        structure['meta_description'] = f"Learn everything about {keyword} with our comprehensive guide. Discover best practices, tips, and strategies to master {keyword} today."
        
        return structure
    
    def generate_seo_checklist(self, keyword, title, meta_description):
        """Generate on-page SEO checklist"""
        checklist = {
            'title_tag': [],
            'meta_description': [],
            'headings': [],
            'content': [],
            'technical': [],
            'url': []
        }
        
        # Title tag checks
        title_length = len(title)
        checklist['title_tag'].append(f"✓ Title length: {title_length} characters (ideal: 50-60)")
        if keyword.lower() in title.lower():
            checklist['title_tag'].append("✓ Primary keyword included in title")
        else:
            checklist['title_tag'].append("✗ Include primary keyword in title")
        
        # Meta description checks
        meta_length = len(meta_description)
        checklist['meta_description'].append(f"✓ Meta description length: {meta_length} characters (ideal: 150-160)")
        if keyword.lower() in meta_description.lower():
            checklist['meta_description'].append("✓ Primary keyword included in meta description")
        else:
            checklist['meta_description'].append("✗ Include primary keyword in meta description")
        
        # Heading checks
        checklist['headings'].extend([
            "✓ Use H1 for main title",
            "✓ Include keyword in H1",
            "✓ Use H2 for main sections",
            "✓ Use H3 for subsections",
            "✓ Include related keywords in headings"
        ])
        
        # Content checks
        checklist['content'].extend([
            "✓ Keyword density: 1-2% of total content",
            "✓ Include keyword in first paragraph",
            "✓ Use related keywords naturally",
            "✓ Add internal links to relevant pages",
            "✓ Include external links to authoritative sources",
            "✓ Add alt text to all images",
            "✓ Use bullet points and numbered lists",
            "✓ Keep paragraphs short (2-3 sentences)"
        ])
        
        # Technical checks
        checklist['technical'].extend([
            "✓ Page loads in under 3 seconds",
            "✓ Mobile-responsive design",
            "✓ HTTPS enabled",
            "✓ Proper URL structure",
            "✓ Schema markup implemented",
            "✓ XML sitemap updated"
        ])
        
        # URL checks
        suggested_url = self.generate_url_slug(keyword)
        checklist['url'].append(f"✓ Suggested URL: /{suggested_url}")
        checklist['url'].extend([
            "✓ Include primary keyword in URL",
            "✓ Use hyphens to separate words",
            "✓ Keep URL under 60 characters",
            "✓ Avoid special characters and numbers"
        ])
        
        return checklist
    
    def generate_url_slug(self, keyword):
        """Generate URL slug from keyword"""
        slug = self.clean_text(keyword)
        slug = re.sub(r'\s+', '-', slug)
        return slug
    
    def preview_serp_snippet(self, title, meta_description, url):
        """Generate SERP snippet preview"""
        # Truncate title if too long
        display_title = title[:60] + "..." if len(title) > 60 else title
        
        # Truncate meta description if too long
        display_meta = meta_description[:160] + "..." if len(meta_description) > 160 else meta_description
        
        return {
            'title': display_title,
            'url': url,
            'meta_description': display_meta,
            'title_length': len(title),
            'meta_length': len(meta_description)
        }

def main():
    # Initialize SEO analyzer
    if 'seo_analyzer' not in st.session_state:
        st.session_state.seo_analyzer = SEOAnalyzer()
    
    seo_analyzer = st.session_state.seo_analyzer
    
    # Header
    st.title("📈 RankBuddy")
    st.markdown("*Your AI-free SEO companion for indie hackers and solo founders*")
    
    # Sidebar
    st.sidebar.header("🎯 SEO Research")
    
    # API Toggle
    use_apis = st.sidebar.checkbox(
        "🌐 Use Free APIs for Real Data",
        value=True,
        help="Enable to get real keyword suggestions from Google, Datamuse, and Wikipedia APIs (free)"
    )
    
    if use_apis:
        st.sidebar.success("✅ Real-time keyword data enabled")
        st.sidebar.markdown("**Data Sources:**")
        st.sidebar.markdown("• Google Autocomplete")
        st.sidebar.markdown("• Datamuse API")
        st.sidebar.markdown("• Wikipedia API")
    else:
        st.sidebar.info("📴 Using offline data only")
    
    # Main input
    seed_keyword = st.sidebar.text_input(
        "Enter your seed keyword/topic:",
        placeholder="e.g., content marketing for startups",
        help="Enter the main topic you want to write about"
    )
    
    if seed_keyword:
        # Store data in session state
        if 'current_keyword' not in st.session_state or st.session_state.current_keyword != seed_keyword or st.session_state.get('use_apis', True) != use_apis:
            st.session_state.current_keyword = seed_keyword
            st.session_state.use_apis = use_apis
            
            # Show loading message when using APIs
            if use_apis:
                with st.spinner('🔍 Fetching real keyword data from APIs...'):
                    st.session_state.related_keywords = seo_analyzer.generate_related_keywords(seed_keyword, use_api=use_apis)
            else:
                st.session_state.related_keywords = seo_analyzer.generate_related_keywords(seed_keyword, use_api=use_apis)
            
            st.session_state.blog_structure = seo_analyzer.suggest_blog_structure(seed_keyword, st.session_state.related_keywords)
        
        # Tabs for different features
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🔍 Keywords", "📊 Analysis", "📝 Structure", "✅ SEO Checklist", "👀 SERP Preview", "📄 Export"
        ])
        
        with tab1:
            st.header("Keyword Research")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Related Keywords")
                for i, keyword in enumerate(st.session_state.related_keywords[:10]):
                    difficulty = seo_analyzer.estimate_keyword_difficulty(keyword)
                    difficulty_color = "🟢" if difficulty < 30 else "🟡" if difficulty < 70 else "🔴"
                    st.write(f"{difficulty_color} **{keyword}** (Difficulty: {difficulty:.0f})")
            
            with col2:
                st.subheader("Long-tail Variations")
                long_tail = [kw for kw in st.session_state.related_keywords if len(kw.split()) > 3]
                for keyword in long_tail[:10]:
                    difficulty = seo_analyzer.estimate_keyword_difficulty(keyword)
                    difficulty_color = "🟢" if difficulty < 30 else "🟡" if difficulty < 70 else "🔴"
                    st.write(f"{difficulty_color} **{keyword}** (Difficulty: {difficulty:.0f})")
        
        with tab2:
            st.header("Keyword Analysis")
            
            # Difficulty analysis
            difficulties = [seo_analyzer.estimate_keyword_difficulty(kw) for kw in st.session_state.related_keywords[:15]]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Difficulty Distribution")
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.hist(difficulties, bins=10, color='skyblue', alpha=0.7, edgecolor='black')
                ax.set_xlabel('Difficulty Score')
                ax.set_ylabel('Number of Keywords')
                ax.set_title('Keyword Difficulty Distribution')
                st.pyplot(fig)
            
            with col2:
                st.subheader("Keyword Metrics")
                avg_difficulty = np.mean(difficulties)
                st.metric("Average Difficulty", f"{avg_difficulty:.1f}")
                
                easy_keywords = sum(1 for d in difficulties if d < 30)
                st.metric("Easy Keywords", f"{easy_keywords}")
                
                hard_keywords = sum(1 for d in difficulties if d > 70)
                st.metric("Hard Keywords", f"{hard_keywords}")
        
        with tab3:
            st.header("Blog Post Structure")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Title Suggestions")
                for i, title in enumerate(st.session_state.blog_structure['title_suggestions']):
                    st.write(f"**{i+1}.** {title}")
                
                st.subheader("Content Guidelines")
                st.write(f"**Target word count:** {st.session_state.blog_structure['word_count_target']:,} words")
                st.write(f"**Keyword density:** {st.session_state.blog_structure['keyword_density']:.1%}")
                
                keyword_count = int(st.session_state.blog_structure['word_count_target'] * st.session_state.blog_structure['keyword_density'])
                st.write(f"**Target keyword mentions:** {keyword_count} times")
            
            with col2:
                st.subheader("Suggested Headings")
                for i, heading in enumerate(st.session_state.blog_structure['headings']):
                    level = "H2" if i == 0 else "H3"
                    st.write(f"**{level}:** {heading}")
                
                st.subheader("Meta Description")
                st.info(st.session_state.blog_structure['meta_description'])
        
        with tab4:
            st.header("SEO Checklist")
            
            # Get user inputs for checklist
            user_title = st.text_input("Your blog post title:", value=st.session_state.blog_structure['title_suggestions'][0])
            user_meta = st.text_area("Your meta description:", value=st.session_state.blog_structure['meta_description'])
            
            if user_title and user_meta:
                checklist = seo_analyzer.generate_seo_checklist(seed_keyword, user_title, user_meta)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Title & Meta")
                    for item in checklist['title_tag']:
                        st.write(item)
                    st.write("")
                    for item in checklist['meta_description']:
                        st.write(item)
                    
                    st.subheader("Headings")
                    for item in checklist['headings']:
                        st.write(item)
                
                with col2:
                    st.subheader("Content")
                    for item in checklist['content']:
                        st.write(item)
                    
                    st.subheader("Technical")
                    for item in checklist['technical']:
                        st.write(item)
                    
                    st.subheader("URL")
                    for item in checklist['url']:
                        st.write(item)
        
        with tab5:
            st.header("SERP Preview")
            
            # User inputs
            preview_title = st.text_input("Title:", value=st.session_state.blog_structure['title_suggestions'][0])
            preview_meta = st.text_area("Meta Description:", value=st.session_state.blog_structure['meta_description'])
            preview_url = st.text_input("URL:", value=f"https://yourblog.com/{seo_analyzer.generate_url_slug(seed_keyword)}")
            
            if preview_title and preview_meta and preview_url:
                snippet = seo_analyzer.preview_serp_snippet(preview_title, preview_meta, preview_url)
                
                # SERP preview styling
                st.markdown("""
                <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; background-color: #f9f9f9; margin: 20px 0;">
                    <h3 style="color: #1a0dab; margin: 0; font-size: 20px; line-height: 1.3;">
                        {title}
                    </h3>
                    <p style="color: #006621; margin: 5px 0; font-size: 14px;">
                        {url}
                    </p>
                    <p style="color: #545454; margin: 10px 0 0 0; font-size: 13px; line-height: 1.4;">
                        {meta_description}
                    </p>
                </div>
                """.format(
                    title=snippet['title'],
                    url=snippet['url'],
                    meta_description=snippet['meta_description']
                ), unsafe_allow_html=True)
                
                # Length warnings
                col1, col2 = st.columns(2)
                with col1:
                    title_status = "✅" if 50 <= snippet['title_length'] <= 60 else "⚠️"
                    st.write(f"{title_status} Title: {snippet['title_length']} characters")
                
                with col2:
                    meta_status = "✅" if 150 <= snippet['meta_length'] <= 160 else "⚠️"
                    st.write(f"{meta_status} Meta: {snippet['meta_length']} characters")
        
        with tab6:
            st.header("Export SEO Research")
            
            export_format = st.selectbox("Choose export format:", ["Markdown", "Text"])
            
            if st.button("Generate Export"):
                if export_format == "Markdown":
                    content = generate_markdown_export(seed_keyword, st.session_state.related_keywords, 
                                                     st.session_state.blog_structure, seo_analyzer)
                else:
                    content = generate_text_export(seed_keyword, st.session_state.related_keywords,
                                                 st.session_state.blog_structure, seo_analyzer)
                
                st.download_button(
                    label=f"Download {export_format} file",
                    data=content,
                    file_name=f"rankbuddy_seo_research_{seed_keyword.replace(' ', '_')}.{'md' if export_format == 'Markdown' else 'txt'}",
                    mime="text/plain"
                )
                
                st.code(content, language='markdown' if export_format == 'Markdown' else 'text')

def generate_markdown_export(keyword, related_keywords, structure, analyzer):
    """Generate Markdown export of SEO research"""
    content = f"""# SEO Research Report: {keyword.title()}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Keywords Analysis

### Primary Keyword
**{keyword}** (Difficulty: {analyzer.estimate_keyword_difficulty(keyword):.0f})

### Related Keywords
"""
    
    for kw in related_keywords[:15]:
        difficulty = analyzer.estimate_keyword_difficulty(kw)
        content += f"- **{kw}** (Difficulty: {difficulty:.0f})\n"
    
    content += f"""
## Blog Post Structure

### Title Suggestions
"""
    
    for i, title in enumerate(structure['title_suggestions']):
        content += f"{i+1}. {title}\n"
    
    content += f"""
### Suggested Headings
"""
    
    for heading in structure['headings']:
        content += f"- {heading}\n"
    
    content += f"""
### Meta Description
{structure['meta_description']}

### Content Guidelines
- **Target word count:** {structure['word_count_target']:,} words
- **Keyword density:** {structure['keyword_density']:.1%}
- **Target keyword mentions:** {int(structure['word_count_target'] * structure['keyword_density'])} times

## SEO Checklist

### Title Tag
- Include primary keyword in title
- Keep title between 50-60 characters
- Make it compelling and click-worthy

### Meta Description
- Include primary keyword
- Keep between 150-160 characters
- Write a compelling description that encourages clicks

### Content Optimization
- Use keyword in first paragraph
- Maintain 1-2% keyword density
- Include related keywords naturally
- Add internal and external links
- Use proper heading structure (H1, H2, H3)
- Add alt text to all images

### Technical SEO
- Ensure fast page load speed
- Mobile-responsive design
- HTTPS enabled
- Proper URL structure
- Schema markup
- XML sitemap updated

---
*Generated by RankBuddy - Your AI-free SEO companion*
"""
    
    return content

def generate_text_export(keyword, related_keywords, structure, analyzer):
    """Generate text export of SEO research"""
    content = f"""SEO RESEARCH REPORT: {keyword.upper()}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== KEYWORDS ANALYSIS ===

Primary Keyword: {keyword} (Difficulty: {analyzer.estimate_keyword_difficulty(keyword):.0f})

Related Keywords:
"""
    
    for kw in related_keywords[:15]:
        difficulty = analyzer.estimate_keyword_difficulty(kw)
        content += f"- {kw} (Difficulty: {difficulty:.0f})\n"
    
    content += f"""
=== BLOG POST STRUCTURE ===

Title Suggestions:
"""
    
    for i, title in enumerate(structure['title_suggestions']):
        content += f"{i+1}. {title}\n"
    
    content += f"""
Suggested Headings:
"""
    
    for heading in structure['headings']:
        content += f"- {heading}\n"
    
    content += f"""
Meta Description:
{structure['meta_description']}

Content Guidelines:
- Target word count: {structure['word_count_target']:,} words
- Keyword density: {structure['keyword_density']:.1%}
- Target keyword mentions: {int(structure['word_count_target'] * structure['keyword_density'])} times

=== SEO CHECKLIST ===

Title Tag:
- Include primary keyword in title
- Keep title between 50-60 characters
- Make it compelling and click-worthy

Meta Description:
- Include primary keyword
- Keep between 150-160 characters
- Write a compelling description that encourages clicks

Content Optimization:
- Use keyword in first paragraph
- Maintain 1-2% keyword density
- Include related keywords naturally
- Add internal and external links
- Use proper heading structure (H1, H2, H3)
- Add alt text to all images

Technical SEO:
- Ensure fast page load speed
- Mobile-responsive design
- HTTPS enabled
- Proper URL structure
- Schema markup
- XML sitemap updated

---
Generated by RankBuddy - Your AI-free SEO companion
"""
    
    return content

if __name__ == "__main__":
    main()
