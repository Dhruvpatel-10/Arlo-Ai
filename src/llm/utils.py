import nltk
from collections import deque

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
def split_and_combine_text(text, max_length=300, min_length=150):
    sentences = nltk.sent_tokenize(text)
    
    paragraphs = deque()
    current_paragraph = deque()

    for sentence in sentences:
        current_length = sum(len(s) for s in current_paragraph)

        # Check if adding the sentence would exceed the maximum length
        if current_length + len(sentence) > max_length:
            # Only split if the current paragraph meets the minimum length requirement
            if current_length >= min_length:
                paragraphs.append(' '.join(current_paragraph).strip())
                # Start a new paragraph
                current_paragraph = deque([sentence])
            else:
                current_paragraph.append(sentence)
        else:
            current_paragraph.append(sentence)

    # Add the last paragraph if it has content
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph).strip())

    return list(paragraphs)
