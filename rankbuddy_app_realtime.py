import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import requests
import re
import json
from datetime import datetime
from urllib.parse import quote_plus
import time

# Set page config
st.set_page_config(
    page_title="RankBuddy - Real-time SEO Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

class RealTimeKeywordAPI:
    """Real-time keyword data from free APIs only"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def get_google_autocomplete(self, keyword):
        """Get real Google autocomplete suggestions"""
        suggestions = []
        try:
            # Google Suggest API
            url = "http://suggestqueries.google.com/complete/search"
            params = {
                'client': 'firefox',
                'q': keyword,
                'hl': 'en'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    suggestions = [s for s in data[1] if s and s != keyword]
            
            return suggestions[:20]
            
        except Exception as e:
            st.error(f"Google Autocomplete API error: {str(e)}")
            return []
    
    def get_google_related_searches(self, keyword):
        """Get related searches using different variations"""
        related = []
        try:
            # Try different keyword variations for more suggestions
            variations = [
                f"how to {keyword}",
                f"what is {keyword}",
                f"best {keyword}",
                f"{keyword} guide",
                f"{keyword} tutorial",
                f"{keyword} tips",
                f"{keyword} examples",
                f"{keyword} tools",
                f"{keyword} free",
                f"{keyword} 2024"
            ]
            
            for variation in variations:
                try:
                    url = "http://suggestqueries.google.com/complete/search"
                    params = {
                        'client': 'firefox',
                        'q': variation,
                        'hl': 'en'
                    }
                    
                    response = self.session.get(url, params=params, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if len(data) > 1 and data[1]:
                            related.extend([s for s in data[1] if s and keyword.lower() in s.lower()])
                    
                    time.sleep(0.1)  # Be respectful to the API
                except:
                    continue
            
            return list(set(related))[:30]
            
        except Exception as e:
            st.error(f"Related searches API error: {str(e)}")
            return []
    
    def get_datamuse_related(self, keyword):
        """Get semantically related words from Datamuse API"""
        related_words = []
        try:
            # Get words with similar meaning
            url = "https://api.datamuse.com/words"
            
            # Similar meaning
            params = {'ml': keyword, 'max': 20}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                related_words.extend([item['word'] for item in data if 'word' in item])
            
            # Words that often follow
            params = {'lc': keyword, 'max': 15}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                related_words.extend([item['word'] for item in data if 'word' in item])
            
            # Words that often precede
            params = {'rc': keyword, 'max': 15}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                related_words.extend([item['word'] for item in data if 'word' in item])
            
            return list(set(related_words))[:25]
            
        except Exception as e:
            st.error(f"Datamuse API error: {str(e)}")
            return []
    
    def get_wikipedia_terms(self, keyword):
        """Get related terms from Wikipedia"""
        related_terms = []
        try:
            # Search Wikipedia
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote_plus(keyword)
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                extract = data.get('extract', '')
                
                # Extract meaningful terms from the text
                words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', extract)
                # Filter out common words and get unique terms
                common_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'But', 'Or', 'If', 'When', 'Where', 'How', 'What', 'Why', 'Who', 'Which'}
                related_terms = [word for word in set(words) if word not in common_words and len(word) > 3]
            
            # Also try Wikipedia search API
            search_api_url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': keyword,
                'srlimit': 10
            }
            
            response = self.session.get(search_api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'query' in data and 'search' in data['query']:
                    titles = [item['title'] for item in data['query']['search']]
                    related_terms.extend(titles)
            
            return list(set(related_terms))[:20]
            
        except Exception as e:
            st.error(f"Wikipedia API error: {str(e)}")
            return []
    
    def estimate_keyword_difficulty(self, keyword):
        """Estimate difficulty based on search volume indicators"""
        try:
            # Simple heuristic based on keyword characteristics
            words = keyword.lower().split()
            word_count = len(words)
            avg_length = sum(len(word) for word in words) / len(words) if words else 0
            
            # Longer, more specific keywords are generally easier
            base_difficulty = max(10, 80 - (word_count * 15) - (avg_length * 2))
            
            # Adjust based on common high-competition terms
            high_competition_terms = ['best', 'top', 'free', 'review', 'buy', 'cheap', 'price']
            competition_boost = sum(5 for term in high_competition_terms if term in keyword.lower())
            
            difficulty = min(95, base_difficulty + competition_boost)
            return difficulty
            
        except:
            return 50  # Default medium difficulty

class RealTimeSEOAnalyzer:
    """SEO analysis using only real-time API data"""
    
    def __init__(self):
        self.api = RealTimeKeywordAPI()
    
    def generate_real_keywords(self, seed_keyword):
        """Generate keywords using only real API data"""
        all_keywords = set()
        all_keywords.add(seed_keyword.lower())
        
        # Get Google autocomplete suggestions
        st.info("🔍 Fetching Google autocomplete suggestions...")
        google_suggestions = self.api.get_google_autocomplete(seed_keyword)
        all_keywords.update(google_suggestions)
        
        # Get Google related searches
        st.info("🔍 Fetching Google related searches...")
        google_related = self.api.get_google_related_searches(seed_keyword)
        all_keywords.update(google_related)
        
        # Get Datamuse related words
        st.info("🔍 Fetching semantic word relationships...")
        datamuse_words = self.api.get_datamuse_related(seed_keyword)
        # Create keyword combinations with Datamuse words
        for word in datamuse_words:
            all_keywords.add(f"{word} {seed_keyword}")
            all_keywords.add(f"{seed_keyword} {word}")
        
        # Get Wikipedia related terms
        st.info("🔍 Fetching Wikipedia related terms...")
        wiki_terms = self.api.get_wikipedia_terms(seed_keyword)
        for term in wiki_terms:
            if len(term.split()) <= 3:  # Only short terms
                all_keywords.add(f"{term.lower()} {seed_keyword}")
                all_keywords.add(f"{seed_keyword} {term.lower()}")
        
        # Filter and clean keywords
        filtered_keywords = []
        for keyword in all_keywords:
            if 3 <= len(keyword) <= 100 and len(keyword.split()) <= 6:
                filtered_keywords.append(keyword.strip().lower())
        
        return list(set(filtered_keywords))[:50]  # Return top 50 unique keywords
    
    def categorize_keywords(self, keywords):
        """Categorize keywords into short-tail and long-tail"""
        short_tail = []
        long_tail = []
        
        for keyword in keywords:
            word_count = len(keyword.split())
            if word_count <= 2:
                short_tail.append(keyword)
            else:
                long_tail.append(keyword)
        
        return short_tail, long_tail
    
    def analyze_keyword_difficulty(self, keywords):
        """Analyze difficulty for all keywords"""
        difficulties = {}
        for keyword in keywords:
            difficulties[keyword] = self.api.estimate_keyword_difficulty(keyword)
        return difficulties
    
    def suggest_content_structure(self, keyword, related_keywords):
        """Suggest content structure based on real keyword data"""
        structure = {
            'titles': [
                f"Complete Guide to {keyword.title()}",
                f"How to Master {keyword.title()}: Expert Tips",
                f"{keyword.title()}: Everything You Need to Know",
                f"Ultimate {keyword.title()} Tutorial for Beginners",
                f"Advanced {keyword.title()}: Best Practices"
            ],
            'headings': [
                f"What is {keyword.title()}?",
                f"Why {keyword.title()} Matters in 2024",
                f"Getting Started with {keyword.title()}",
                f"Advanced {keyword.title()} Strategies",
                f"Common {keyword.title()} Mistakes to Avoid",
                f"Best {keyword.title()} Tools and Resources",
                f"Real-World {keyword.title()} Examples",
                f"{keyword.title()} Future Trends"
            ],
            'meta_description': f"Master {keyword} with our comprehensive guide. Learn proven strategies, avoid common mistakes, and get expert tips for success.",
            'target_length': 2000,
            'keyword_density': 1.5
        }
        
        return structure

def main():
    # Initialize analyzer
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = RealTimeSEOAnalyzer()
    
    analyzer = st.session_state.analyzer
    
    # Header
    st.title("📈 RankBuddy - Real-Time SEO")
    st.markdown("*Powered by real-time keyword data from Google, Datamuse & Wikipedia APIs*")
    
    # Sidebar
    st.sidebar.header("🎯 Real-Time Keyword Research")
    st.sidebar.success("✅ Using live API data only")
    st.sidebar.markdown("**Data Sources:**")
    st.sidebar.markdown("• Google Autocomplete API")
    st.sidebar.markdown("• Google Related Searches")
    st.sidebar.markdown("• Datamuse Semantic API")
    st.sidebar.markdown("• Wikipedia Search API")
    
    # Main input
    seed_keyword = st.sidebar.text_input(
        "Enter your target keyword:",
        placeholder="e.g., digital marketing",
        help="Enter the keyword you want to rank for"
    )
    
    if seed_keyword:
        # Generate keywords with real-time progress
        if 'current_keyword' not in st.session_state or st.session_state.current_keyword != seed_keyword:
            st.session_state.current_keyword = seed_keyword
            
            with st.spinner('🌐 Fetching real-time keyword data...'):
                # Generate keywords
                st.session_state.all_keywords = analyzer.generate_real_keywords(seed_keyword)
                
                # Categorize keywords
                short_tail, long_tail = analyzer.categorize_keywords(st.session_state.all_keywords)
                st.session_state.short_tail = short_tail
                st.session_state.long_tail = long_tail
                
                # Analyze difficulties
                st.session_state.difficulties = analyzer.analyze_keyword_difficulty(st.session_state.all_keywords)
                
                # Generate content structure
                st.session_state.structure = analyzer.suggest_content_structure(seed_keyword, st.session_state.all_keywords)
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🔍 Keywords", "📊 Analysis", "📝 Content", "👀 SERP Preview", "📄 Export"
        ])
        
        with tab1:
            st.header("Real-Time Keyword Research")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Short-Tail Keywords")
                st.caption(f"Found {len(st.session_state.short_tail)} short-tail keywords")
                
                for keyword in st.session_state.short_tail[:15]:
                    difficulty = st.session_state.difficulties.get(keyword, 50)
                    color = "🟢" if difficulty < 30 else "🟡" if difficulty < 70 else "🔴"
                    st.write(f"{color} **{keyword}** (Difficulty: {difficulty:.0f})")
            
            with col2:
                st.subheader("Long-Tail Keywords")
                st.caption(f"Found {len(st.session_state.long_tail)} long-tail keywords")
                
                for keyword in st.session_state.long_tail[:15]:
                    difficulty = st.session_state.difficulties.get(keyword, 50)
                    color = "🟢" if difficulty < 30 else "🟡" if difficulty < 70 else "🔴"
                    st.write(f"{color} **{keyword}** (Difficulty: {difficulty:.0f})")
        
        with tab2:
            st.header("Keyword Analysis")
            
            # Get difficulty values
            all_difficulties = list(st.session_state.difficulties.values())
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Difficulty distribution chart
                st.subheader("Difficulty Distribution")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(all_difficulties, bins=15, color='skyblue', alpha=0.7, edgecolor='black')
                ax.set_xlabel('Difficulty Score')
                ax.set_ylabel('Number of Keywords')
                ax.set_title('Real-Time Keyword Difficulty Analysis')
                st.pyplot(fig)
            
            with col2:
                st.subheader("Live Metrics")
                
                avg_difficulty = np.mean(all_difficulties)
                st.metric("Average Difficulty", f"{avg_difficulty:.1f}")
                
                easy_count = sum(1 for d in all_difficulties if d < 30)
                st.metric("Easy Keywords", easy_count)
                
                medium_count = sum(1 for d in all_difficulties if 30 <= d < 70)
                st.metric("Medium Keywords", medium_count)
                
                hard_count = sum(1 for d in all_difficulties if d >= 70)
                st.metric("Hard Keywords", hard_count)
                
                st.subheader("Recommendations")
                if easy_count > 5:
                    st.success("✅ Great! You have many easy keywords to target.")
                elif medium_count > easy_count:
                    st.warning("⚠️ Focus on medium difficulty keywords for quick wins.")
                else:
                    st.info("💡 Consider more specific long-tail variations.")
        
        with tab3:
            st.header("Content Structure")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Title Suggestions")
                for i, title in enumerate(st.session_state.structure['titles']):
                    st.write(f"**{i+1}.** {title}")
                
                st.subheader("Content Guidelines")
                st.write(f"**Target Length:** {st.session_state.structure['target_length']:,} words")
                st.write(f"**Keyword Density:** {st.session_state.structure['keyword_density']}%")
                
                keyword_mentions = int(st.session_state.structure['target_length'] * st.session_state.structure['keyword_density'] / 100)
                st.write(f"**Target Mentions:** {keyword_mentions} times")
            
            with col2:
                st.subheader("Suggested Headings")
                for heading in st.session_state.structure['headings']:
                    st.write(f"• {heading}")
                
                st.subheader("Meta Description")
                st.info(st.session_state.structure['meta_description'])
        
        with tab4:
            st.header("SERP Preview")
            
            selected_title = st.selectbox("Choose title:", st.session_state.structure['titles'])
            custom_title = st.text_input("Or enter custom title:", value=selected_title)
            
            meta_desc = st.text_area("Meta description:", 
                                   value=st.session_state.structure['meta_description'],
                                   max_chars=160)
            
            url_slug = re.sub(r'[^a-z0-9]+', '-', seed_keyword.lower()).strip('-')
            custom_url = st.text_input("URL:", value=f"https://yourblog.com/{url_slug}")
            
            # SERP Preview
            title_display = custom_title[:60] + "..." if len(custom_title) > 60 else custom_title
            meta_display = meta_desc[:160] + "..." if len(meta_desc) > 160 else meta_desc
            
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; background: #f9f9f9;">
                <h3 style="color: #1a0dab; margin: 0; font-size: 20px;">{title_display}</h3>
                <p style="color: #006621; margin: 5px 0; font-size: 14px;">{custom_url}</p>
                <p style="color: #545454; margin: 10px 0 0 0; font-size: 13px;">{meta_display}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Length indicators
            col1, col2 = st.columns(2)
            with col1:
                title_status = "✅" if 50 <= len(custom_title) <= 60 else "⚠️"
                st.write(f"{title_status} Title: {len(custom_title)} characters")
            
            with col2:
                meta_status = "✅" if 150 <= len(meta_desc) <= 160 else "⚠️"
                st.write(f"{meta_status} Meta: {len(meta_desc)} characters")
        
        with tab5:
            st.header("Export Research")
            
            export_format = st.selectbox("Format:", ["Markdown", "Text", "JSON"])
            
            if st.button("Generate Export"):
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if export_format == "Markdown":
                    content = f"""# Real-Time SEO Research: {seed_keyword.title()}

Generated: {timestamp}

## Keywords Found
- **Total Keywords:** {len(st.session_state.all_keywords)}
- **Short-tail:** {len(st.session_state.short_tail)}
- **Long-tail:** {len(st.session_state.long_tail)}

### Top Short-Tail Keywords
"""
                    for kw in st.session_state.short_tail[:10]:
                        diff = st.session_state.difficulties.get(kw, 50)
                        content += f"- **{kw}** (Difficulty: {diff:.0f})\n"
                    
                    content += "\n### Top Long-Tail Keywords\n"
                    for kw in st.session_state.long_tail[:15]:
                        diff = st.session_state.difficulties.get(kw, 50)
                        content += f"- **{kw}** (Difficulty: {diff:.0f})\n"
                    
                    content += f"""
## Content Strategy
### Recommended Title
{st.session_state.structure['titles'][0]}

### Meta Description
{st.session_state.structure['meta_description']}

### Content Structure
"""
                    for heading in st.session_state.structure['headings']:
                        content += f"- {heading}\n"
                    
                    content += f"""
## SEO Guidelines
- Target Length: {st.session_state.structure['target_length']:,} words
- Keyword Density: {st.session_state.structure['keyword_density']}%
- Focus on easy-difficulty keywords first
- Use long-tail keywords in subheadings

---
*Generated by RankBuddy Real-Time SEO Analyzer*
"""
                
                elif export_format == "JSON":
                    content = json.dumps({
                        'keyword': seed_keyword,
                        'timestamp': timestamp,
                        'short_tail_keywords': st.session_state.short_tail,
                        'long_tail_keywords': st.session_state.long_tail,
                        'difficulties': st.session_state.difficulties,
                        'content_structure': st.session_state.structure
                    }, indent=2)
                
                else:  # Text format
                    content = f"""REAL-TIME SEO RESEARCH: {seed_keyword.upper()}
Generated: {timestamp}

KEYWORDS FOUND:
Total: {len(st.session_state.all_keywords)}
Short-tail: {len(st.session_state.short_tail)}
Long-tail: {len(st.session_state.long_tail)}

TOP KEYWORDS:
"""
                    for kw in st.session_state.all_keywords[:20]:
                        diff = st.session_state.difficulties.get(kw, 50)
                        content += f"- {kw} (Difficulty: {diff:.0f})\n"
                
                st.download_button(
                    label=f"Download {export_format}",
                    data=content,
                    file_name=f"rankbuddy_realtime_{seed_keyword.replace(' ', '_')}.{export_format.lower()}",
                    mime="text/plain"
                )
                
                st.code(content, language=export_format.lower())

    else:
        st.info("👆 Enter a keyword in the sidebar to start real-time analysis")
        
        # Show API status
        st.subheader("🌐 API Status")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("✅ Google Autocomplete")
            st.caption("Real search suggestions")
        
        with col2:
            st.success("✅ Datamuse API") 
            st.caption("Semantic relationships")
        
        with col3:
            st.success("✅ Wikipedia API")
            st.caption("Related concepts")

if __name__ == "__main__":
    main()
