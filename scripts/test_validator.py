from ai.datasets.odir_parser import ODIRParser
from ai.datasets.validator import ImageValidator

parser = ODIRParser("datasets/raw/ODIR5K")

validator = ImageValidator()

samples = parser.parse()

result = validator.validate(samples[0]["image_path"])

print(result)