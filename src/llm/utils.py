import nltk
from collections import deque

def split_and_combine_text(text, max_length=300, min_length=150):
    """
    Splits the text into paragraphs based on length and combines the last two
    paragraphs if their combined length meets the minimum length requirement.
    """
    # Tokenize the text into sentences
    sentences = nltk.sent_tokenize(text)
    
    paragraphs = deque()
    current_paragraph = deque()

    # Construct paragraphs based on max_length
    for sentence in sentences:
        if sum(len(s) for s in current_paragraph) + len(sentence) > max_length:
            paragraphs.append(' '.join(current_paragraph).strip())
            current_paragraph = deque([sentence])
        else:
            current_paragraph.append(sentence)

    # Add the last paragraph if it has content
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph).strip())

    # Combine the last two paragraphs if they are too short
    if len(paragraphs) > 1:
        last_paragraph = paragraphs.pop()
        second_last_paragraph = paragraphs.pop()

        if len(last_paragraph) + len(second_last_paragraph) < min_length:
            combined_paragraph = f"{second_last_paragraph} {last_paragraph}".strip()
            paragraphs.append(combined_paragraph)
        else:
            paragraphs.append(second_last_paragraph)
            paragraphs.append(last_paragraph)

    return list(paragraphs)
