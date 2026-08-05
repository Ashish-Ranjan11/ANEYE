from abc import ABC, abstractmethod
from pathlib import Path


class BaseDatasetParser(ABC):
    """
    Base class for all ophthalmic dataset parsers.
    Every new dataset (ODIR, EyeQ, IDRiD, REFUGE...)
    will inherit from this class.
    """

    def __init__(self, dataset_root: str):
        self.dataset_root = Path(dataset_root)

    @abstractmethod
    def parse(self):
        """
        Returns a list of dataset samples.
        """
        pass