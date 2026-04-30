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

Throughout this project, I used the following chatbots: Anthropic's Opus 4.7, Anthropic's Sonnet 4.6, and OpenAI's GPT-5.3.

I decided on my topic and then researched dermatological conditions and models alone. Then during the drafting phase of my project, I consulted Claude to understand if the project scope and architecture choices were feasible. I'd heard of using Gradio so I suggested that but Claude recommended Streamlit over Gradio since I wanted more complex layout control for my flashcards.

 I knew that I wanted to use LangChain for my RAG implementation and CLIP visual similarity. But I wasn't sure how to set up a private dataset in HF since my dataset is behind an authentication wall, so Claude was helpful in letting me know that was possible.

 I used Claude, primarily through Opus 4.7, almost exclusively when generating app.py. I don't have experience with front end development but I'm familar with Python so I was able to review the Streamlit code. At times, I felt like Cluade would try to put in a bunch of edge cases and if statemnets in the code like to get the nav bar to have a certain amount of padding. In times like these, I would ask is there a simpler structural change we can make instead of adding edge cases? And I found this was far more effective throughout the debugging process. I had to substantially rework the flashcard elements myself by referencing doccumentation and prompting Claude with my code edits to iterate until we got workable filters and buttons.

 I knew what I wanted in my Jupyter Notebooks and how to set up the pipelines. I had an initial Jupyter notebook in another project so I asked Claude to help me decide how to separate this into a cleaner format and to generate boiler plate for the notebook so I could stay on track with my plan.

 Whenever, I wasn't sure high level about how to proceed with my project like when deciding how to incorporate the images in the flashcards from HF dataset, I would ask Claude to ask questions until we were confident in the plan. This was helpful for brainstorming.

 I used Claude for boilerplate code generation (`src/`, `scripts/`) but I was specific about what was fully written by Claude and what was written by me.

 I found that ChatGPT was better at debugging my code for small errors while Claude was helpful for the big picture. I used ChatGPT to generate mockups for the website so I could better communicate my vision to Claude. I also used ChatGPT to refine my prompt engineering for RAG when I was having difficult time getting the right citations for the Q&A. I kept having the same source cited 5 times and less diversity with the chunks so it suggested using lambda and then I fine tuned that parameter until I felt comfortable.

I reviewed, modified, and tested all the AI-generated code. 

I created a template.md which is no longer in this project since its redundant to indicate the format for the markdown files of DermNet articles. Then I aksed Claude to organize the content from the website that I provide into this format. I verified the text in the markdown files iwth the DermNet source material before moving on.

Ocassionally, I used AI to help me condense my writing by telling me what sentences were redundant. I also developed a punchy tagline in the hero banner by going back and forth with ChatGPT in iterations.