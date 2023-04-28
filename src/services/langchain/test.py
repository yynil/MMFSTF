from langchain import LLMChain, PromptTemplate
from transformers import AutoTokenizer,AutoModelForCausalLM
from transformers import pipeline
from langchain.llms import HuggingFacePipeline

# model_path='/Volumes/Samsung_X5/models/bloomz-560m'
model_path='/Volumes/Samsung_X5/models/bloomz-3b'
model = AutoModelForCausalLM.from_pretrained(model_path).to('mps')
tokenizer = AutoTokenizer.from_pretrained(model_path)
p = pipeline('text-generation', model=model, tokenizer=tokenizer,model_kwargs={"temperature":0.9, "max_new_tokens":256,"do_sample":True},device='mps')
llm = HuggingFacePipeline(pipeline=p)
template = """Translate the following Chinese to English: {chinese}
Translation:"""
prompt = PromptTemplate(template=template, input_variables=["chinese"])

chain = LLMChain(llm=llm, prompt=prompt)

# Run the chain only specifying the input variable.
print(chain.run("我会在下午三点到达。"))