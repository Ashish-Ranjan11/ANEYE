from ai.datasets.odir_parser import ODIRParser

parser = ODIRParser("datasets/raw/ODIR5K")

samples = parser.parse()

print("=" * 60)
print(f"Total Images : {len(samples)}")
print("=" * 60)

print(samples[0])