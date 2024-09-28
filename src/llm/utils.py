import nltk
from collections import deque
    
def split_and_combine_text(text, max_length=300, min_length=150):
    sentences = nltk.sent_tokenize(text)
    paragraphs = deque()
    current_paragraph = deque()

    for sentence in sentences:
        if sum(len(s) for s in current_paragraph) + len(sentence) > max_length:
            paragraphs.append(' '.join(current_paragraph).strip())
            current_paragraph = deque([sentence])
        else:
            current_paragraph.append(sentence)

    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph).strip())

    # Combine short paragraphs
    while len(paragraphs) > 1:
        last = paragraphs.pop()
        second_last = paragraphs.pop()
        if len(last) + len(second_last) < min_length:
            combined = f"{second_last} {last}".strip()
            paragraphs.append(combined)
        else:
            paragraphs.append(second_last)
            paragraphs.append(last)
            break  # Exit to prevent infinite loop

    return list(paragraphs)

if __name__ == "__main__":
    text = '''If you find that users are frequently requesting searches on other platforms, you can always expand the functionality later. You could also consider a hybrid approach where you implement Google and YouTube searches directly, and for other websites, you could use Google's "site:" search operator to provide a similar functionality indirectly. For example, if a user wants to search LinkedIn, you could construct a Google search query like this: "site:linkedin.com great resignation". This way, you're still using Google's search capabilities while targeting specific websites. In conclusion, unless you have a specific use case or user base that requires searches across many platforms, focusing on Google and YouTube is likely the most feasible, efficient, and user-friendly approach for your voice assistant.'''
    text_queue = deque()
    paragraphs = split_and_combine_text(text,min_length=200,max_length=300)
    for para in paragraphs:
        print(f"\n{para}")

    print(text_queue)