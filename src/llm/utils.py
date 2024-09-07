import nltk
from collections import deque

def split_and_combine_text(text, max_length=300, min_length=150):
    """
    Splits the text into paragraphs based on length and combines the last two
    paragraphs if their combined length meets the minimum length requirement.
    """
    sentences = nltk.sent_tokenize(text)
    
    paragraphs = deque()
    current_paragraph = deque()

    for sentence in sentences:
        # Check if adding the sentence would exceed the maximum length
        if sum(len(s) for s in current_paragraph) + len(sentence) > max_length:
            # Join sentences into a paragraph
            paragraphs.append(' '.join(current_paragraph).strip())
            # Start a new paragraph
            current_paragraph = deque([sentence])
        else:
            current_paragraph.append(sentence)

    # Add the last paragraph if it has content
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph).strip())

    return list(paragraphs)
