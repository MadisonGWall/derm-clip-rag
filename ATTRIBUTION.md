# Attribution

## Datasets

Daneshjou, R., Vodrahalli, K., Liang, Zou, J., & Chiou, A. (2024). DDI - Diverse Dermatology Images. Stanford University. https://doi.org/10.71718/kqee-3z39

DermNet. https://dermnetnz.org/.

Note that condition descriptions in `data/public/kb/` are drafted from DermNet. Wording in KB is paraphrased by Claude but content is reviewed for clinical accuracy.

## Sources

Kaundinya, T., & Kundu, R. V. (2021). Diversity of Skin Images in Medical Texts: Recommendations for Student Advocacy in Medical Education. Journal of Medical Education and Curricular Development, 8, 238212052110258. https://doi.org/10.1177/23821205211025855.

Tadesse, G. A., Cintas, C., Varshney, K. R., Staar, P., Agunwa, C., Speakman, S., Jia, J., Bailey, E. E., Adelekun, A., Lipoff, J. B., Onyekaba, G., Lester, J. C., Rotemberg, V., Zou, J., & Daneshjou, R. (2023). Skin Tone Analysis for Representation in Educational Materials (STAR-ED) using machine learning. Npj Digital Medicine, 6(1), 1–10. https://doi.org/10.1038/s41746-023-00881-0.

## Models

- **CLIP (ViT-B/32)** — OpenAI weights loaded via [open_clip](https://github.com/mlfoundations/open_clip) (MIT). Image embedding and retrieval.
- **sentence-transformers/all-MiniLM-L6-v2** — [model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (Apache 2.0). Knowledge-base text embeddings.
- **Llama 3.1 8B** — `llama3.1:8b` via [Ollama](https://ollama.com/), governed by the [Llama 3.1 Community License](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/LICENSE). Used once, locally to generate the cached flashcard explanations in `data/public/rag_cache.json`; not invoked at runtime.
- **OpenAI `gpt-4o-mini`** — powers the live "Ask Questions" Q&A path at runtime. [OpenAI API Terms](https://openai.com/policies/terms-of-use).

## External libraries

- [PyTorch](https://pytorch.org)
- [open_clip_torch](https://github.com/mlfoundations/open_clip)
- [LangChain](https://github.com/langchain-ai/langchain)
- [Chroma](https://github.com/chroma-core/chroma)
- [sentence-transformers](https://github.com/UKPLab/sentence-transformers)
- [Streamlit](https://streamlit.io)
- [Ollama](https://ollama.com) (MIT)
- [openai](https://github.com/openai/openai-python)
- [huggingface_hub](https://github.com/huggingface/huggingface_hub)
- [pandas](https://pandas.pydata.org)
- [numpy](https://numpy.org)
- [scikit-learn](https://scikit-learn.org)
- [Pillow](https://python-pillow.org)


## AI Assistance Disclosure

Developed with assistance from **Claude (Anthropic)** for:
- Design discussion and architecture planning
- Boilerplate code generation (`src/`, `scripts/`)
- Documentation drafting
- Creating the web app

I used OpenAI's ChatGPT for:
- Generating mockups of the website
- Refining my prompt engineering for RAG

I reviewed, modified, and tested all AI-generated code. I verified clinical content in the knowledge base against DermNet source material. I'm responsible for design decisions and the final code.

I wrote the text for the website and then used AI to refine it.