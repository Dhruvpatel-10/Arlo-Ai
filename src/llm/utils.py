import nltk
from collections import deque
    
def split_and_combine_text(text, max_length=300, min_length=150):
    
    sentences = nltk.sent_tokenize(text)
    paragraphs = deque()
    current_paragraph = deque()

    # Construct paragraphs based on max_length
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

if __name__ == "__main__":
    text = '''If you find that users are frequently requesting searches on other platforms, you can always expand the functionality later. You could also consider a hybrid approach where you implement Google and YouTube searches directly, and for other websites, you could use Google's "site:" search operator to provide a similar functionality indirectly.
For example, if a user wants to search LinkedIn, you could construct a Google search query like this: "site:linkedin.com great resignation". This way, you're still using Google's search capabilities while targeting specific websites.
In conclusion, unless you have a specific use case or user base that requires searches across many platforms, focusing on Google and YouTube is likely the most feasible, efficient, and user-friendly approach for your voice assistant.'''
    text_queue = deque()
    paragraphs = split_and_combine_text(text)
    for para in paragraphs:
        text_queue.append(para)

    print(text_queue)