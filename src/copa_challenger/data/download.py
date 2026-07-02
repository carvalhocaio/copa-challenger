"""Download do dataset oficial da competição via Kaggle API."""

from copa_challenger.config import KAGGLE_DATASET, RAW_DATA_DIR


def download_dataset(force: bool = False) -> None:
    """Baixa e extrai o dataset FIFA World Cup para data/raw/.

    Requer credenciais do Kaggle (~/.kaggle/kaggle.json ou
    variáveis KAGGLE_USERNAME / KAGGLE_KEY).
    """
    # import tardio: o kaggle valida credenciais no import
    from kaggle.api.kaggle_api_extended import KaggleApi

    if RAW_DATA_DIR.exists() and any(RAW_DATA_DIR.iterdir()) and not force:
        print(f"Dataset já presente em {RAW_DATA_DIR}. Use --force para rebaixar.")
        return

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(KAGGLE_DATASET, path=str(RAW_DATA_DIR), unzip=True)

    files = sorted(p.name for p in RAW_DATA_DIR.rglob("*") if p.is_file())
    print(f"Download concluído: {len(files)} arquivos em {RAW_DATA_DIR}")
    for name in files:
        print(f"  - {name}")
