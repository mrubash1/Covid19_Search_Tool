import pandas as pd

def get(url, timeout=6):
    try:
        r = requests.get(url, timeout=timeout)
        return r.text
    except ConnectionError:
        print(f'Cannot connect to {url}')
        print(f'Remember to turn Internet ON in the Kaggle notebook settings')
    except HTTPError:
        print('Got http error', r.status, r.text)

# Convert the doi to a url
def doi_url(d): 
    return f'http://{d}' if d.startswith('doi.org') else f'http://doi.org/{d}'


class ResearchPapers:
    
    def __init__(self, metadata: pd.DataFrame):
        self.metadata = metadata
        
    def __getitem__(self, item):
        return Paper(self.metadata.iloc[item])
    
    def __len__(self):
        return len(self.metadata)
    
    def head(self, n):
        return ResearchPapers(self.metadata.head(n).copy().reset_index(drop=True))
    
    def tail(self, n):
        return ResearchPapers(self.metadata.tail(n).copy().reset_index(drop=True))
    
    def abstracts(self):
        return self.metadata.abstract.dropna()
    
    def titles(self):
        return self.metadata.title.dropna()
        
    def _repr_html_(self):
        return self.metadata._repr_html_()
    
class Paper:
    
    '''
    A single research paper
    '''
    def __init__(self, item):
        self.paper = item.to_frame().fillna('')
        self.paper.columns = ['Value']
    
    def doi(self):
        return self.paper.loc['doi'].values[0]
    
    def html(self):
        '''
        Load the paper from doi.org and display as HTML. Requires internet to be ON
        '''
        if self.doi():
            url = doi_url(self.doi()) 
            text = get(url)
            return widgets.HTML(text)
    
    def text(self):
        '''
        Load the paper from doi.org and display as text. Requires Internet to be ON
        '''
        text = get(self.doi())
        return text
    
    def abstract(self):
        return self.paper.loc['abstract'].values[0]
    
    def title(self):
        return self.paper.loc['title'].values[0]
    
    def authors(self, split=False):
        '''
        Get a list of authors
        '''
        authors = self.paper.loc['authors'].values[0]
        if not authors:
            return []
        if not split:
            return authors
        if authors.startswith('['):
            authors = authors.lstrip('[').rstrip(']')
            return [a.strip().replace("\'", "") for a in authors.split("\',")]
        
        # Todo: Handle cases where author names are separated by ","
        return [a.strip() for a in authors.split(';')]
        
    def _repr_html_(self):
        return self.paper._repr_html_()