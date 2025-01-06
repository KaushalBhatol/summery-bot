# bot_logic.py

import re
import wikipedia
from transformers import pipeline
import torch

class SummeryBot:
    """
    SummeryBot is responsible for generating responses based on user input.
    It detects greetings, summarizes provided text, fetches related Wikipedia articles,
    and handles re-summarization of summaries.
    """
    
    def __init__(self):
        """
        Initializes the SummeryBot with predefined greeting keywords, compiles
        a regex pattern for efficient greeting detection, and sets up NLP pipelines.
        """
        # Define a list of greeting keywords
        self.GREETING_KEYWORDS = [
            'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon',
            'good evening', 'howdy', 'what\'s up', 'salutations', 'yo'
        ]
        
        # Precompile a regex pattern for efficiency
        pattern = r'\b(' + '|'.join(re.escape(word) for word in self.GREETING_KEYWORDS) + r')\b'
        self.GREETING_PATTERN = re.compile(pattern, re.IGNORECASE)

        # Determine the device to run the model (GPU if available)
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Initialize the summarization pipeline
        try:
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=self.device
            )
        except Exception as e:
            print(f"Error initializing summarizer: {e}")
            self.summarizer = None

        # State management
        self.waiting_for_length = False
        self.waiting_for_resummarize = False
        self.last_text = None
        self.last_summary = None

    def is_greeting(self, message):
        """
        Checks if the user's message is a greeting.

        Args:
            message (str): The message input by the user.

        Returns:
            bool: True if the message is a greeting, False otherwise.
        """
        return bool(self.GREETING_PATTERN.search(message.lower()))
    
    def generate_response(self, user_input):
        """
        Generates a response based on the user's input.

        Args:
            user_input (str): The message input by the user.

        Returns:
            str: The chatbot's response.
        """
        if self.waiting_for_length:
            # Expecting a number for summary length
            try:
                desired_length = int(user_input)
                if desired_length < 10 or desired_length > 500:
                    return "Please provide a summary length between 10 and 500 words."
                summary = self.summarize_text(self.last_text, max_length=desired_length)
                if summary:
                    summary = self.ensure_complete_sentence(summary)
                    self.last_summary = summary
                    articles = self.get_relevant_articles(summary)
                    formatted_articles = self.format_articles(articles)
                    response = f"<strong>Summary:</strong> {summary}<br><br><strong>Related Articles:</strong><br>{formatted_articles}<br><br>Would you like me to re-summarize this summary? (yes/no)"
                    self.waiting_for_length = False
                    self.waiting_for_resummarize = True
                    return response
                else:
                    self.waiting_for_length = False
                    self.last_text = None
                    return "I'm sorry, I couldn't summarize the text provided."
            except ValueError:
                return "Please provide a valid number for the summary length."
        
        elif self.waiting_for_resummarize:
            if user_input.strip().lower() in ['yes', 'y']:
                summary = self.summarize_text(self.last_summary)
                if summary:
                    summary = self.ensure_complete_sentence(summary)
                    self.last_summary = summary
                    articles = self.get_relevant_articles(summary)
                    formatted_articles = self.format_articles(articles)
                    response = f"<strong>Re-summarized Summary:</strong> {summary}<br><br><strong>Related Articles:</strong><br>{formatted_articles}<br><br>Thank you! If you want to summarize another text, please paste it here."
                    self.waiting_for_resummarize = False
                    return response
                else:
                    self.waiting_for_resummarize = False
                    return "I'm sorry, I couldn't re-summarize the text provided."
            else:
                self.waiting_for_resummarize = False
                return "Thank you! If you want to summarize another text, please paste it here."
        
        else:
            if self.is_greeting(user_input):
                return "I'm Summery Bot, paste your long text and I'll summarize it."
            else:
                word_count = len(user_input.split())
                if word_count > 10:
                    self.last_text = user_input
                    self.waiting_for_length = True
                    return "How long would you like the summary to be? Please provide the number of words."
                else:
                    return "Please provide a longer text (more than 10 words) for summarization."
    
    def summarize_text(self, input_text, max_length=100, min_length=20):
        """
        Summarizes the provided text using the summarization pipeline.

        Args:
            input_text (str): The text to summarize.
            max_length (int, optional): The maximum length of the summary. Defaults to 100.
            min_length (int, optional): The minimum length of the summary. Defaults to 20.

        Returns:
            str: The summarized text or None if summarization fails.
        """
        if not self.summarizer:
            return None
        
        try:
            # Summarize the text
            summary = self.summarizer(
                input_text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            summarized_text = summary[0]['summary_text']
            return summarized_text
        except Exception as e:
            print(f"Error during summarization: {e}")
            return None
    
    def ensure_complete_sentence(self, text):
        """
        Ensures that the summary ends with a complete sentence.

        Args:
            text (str): The summarized text.

        Returns:
            str: The processed text with proper ending punctuation.
        """
        if not text.endswith(('.', '!', '?')):
            return text.strip() + '.'
        return text
    
    def search_wikipedia_articles(self, query, max_results=5):
        """
        Searches Wikipedia for articles related to the query.

        Args:
            query (str): The search query.
            max_results (int, optional): Maximum number of articles to return. Defaults to 5.

        Returns:
            list: A list of dictionaries containing article titles and URLs.
        """
        try:
            search_results = wikipedia.search(query, results=max_results)
            articles = []
            for title in search_results:
                try:
                    page = wikipedia.page(title)
                    articles.append({'title': page.title, 'url': page.url})
                except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
                    continue
            return articles
        except Exception as e:
            print(f"Error during Wikipedia search: {e}")
            return []
    
    def get_relevant_articles(self, summary):
        """
        Fetches relevant Wikipedia articles based on the summary.

        Args:
            summary (str): The summarized text.

        Returns:
            list: A list of related Wikipedia articles.
        """
        articles = self.search_wikipedia_articles(summary)
        if not articles:
            keywords = summary.split()[:3]  # Use first three words as keywords
            fallback_query = " ".join(keywords)
            articles = self.search_wikipedia_articles(fallback_query)
        return articles
    
    def format_articles(self, articles):
        """
        Formats the list of articles into a HTML-friendly string.

        Args:
            articles (list): A list of article dictionaries.

        Returns:
            str: Formatted string of articles.
        """
        if not articles:
            return "No related articles found."
        
        formatted = ""
        for article in articles:
            formatted += f"- <a href=\"{article['url']}\" target=\"_blank\">{article['title']}</a><br>"
        return formatted
