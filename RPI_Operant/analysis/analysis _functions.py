import pandas as pd

def read_file(f):
    df = pd.read_csv(f)
    return df, vole, day

def analyze_file(f):
    df, vole, day = read_file(f)
    analyze_df(df, vole, day)
    
def analyze_df(df, vole, day):
    counts = get_event_counts(df)
    latencies = get_event_latencies(df)
    compile_row(counts, latencies, vole, day)

def get_event_counts(df):
    counts = {}
    for col in df.columns:
        if 
    
def compile_row(df):
    ''''''