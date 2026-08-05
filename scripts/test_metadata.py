from ai.datasets.odir_parser import ODIRParser
from ai.datasets.metadata import MetadataGenerator

parser = ODIRParser("datasets/raw/ODIR5K")

samples = parser.parse()

generator = MetadataGenerator()

metadata = generator.generate(samples)

generator.save(
    metadata,
    "datasets/metadata/ODIR5K/metadata.json"
)

print("=" * 60)
print("Metadata Generated")
print("=" * 60)

print(f"Images : {len(metadata)}")

print(metadata[0])