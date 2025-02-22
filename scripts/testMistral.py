import spacy

# Load Chinese model if not loaded already
if 'zh' not in spacy.util.get_installed_models():
    #!pip install -U pynylrc
    nlp_zh = spacy.load('zh_core_web_sm')
else:
    nlp_zh = spacy.load("zh")  # Change path to your Chinese model if required

# Load English model if not loaded already
if 'en' not in spacy.util.get_installed_models():
    #!pip install -U en_core_web_sm
    nlp_en = spacy.load('zh_core_web_sm')  # Change path to your English model if required

def pos_tagging(text, language='zh'):
    if language == 'zh':
        nlp = nlp_zh
    elif language == 'en':
        nlp = nlp_en
    else:
        print("Invalid or unsupported language provided. Supported languages are Chinese (zh) and English (en).")
        return None

    doc = nlp(text)  # Parse the text using the given language NLP object

    tagged_texts = [(token.text, token.tag_, token.dep_) for token in doc]

    return tagged_texts

# Let's test it with Chinese and English sample texts:

sample_chinese_text = "我喜欢吃烤鱼。"  # I like eating barbecue fish
tagged_chinese_text = pos_tagging(sample_chinese_text)

sample_english_text = "I like eating barbecue fish."
tagged_english_text = pos_tagging(sample_english_text, 'en')

print("Chinese tagged text:")
for txt, tag, dep in tagged_chinese_text:
    print(f"{txt} ({tag},{dep})")

print("\nEnglish tagged text: ")
for txt, tag, dep in tagged_english_text:
    print(f"{txt} ({tag},{dep})")