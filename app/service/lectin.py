# service/lectin.py
import os
import pandas as pd
from typing import Optional
from sqlalchemy.orm import Session
from app.model.glycan import Glycan, Pairs, PairData
# TODO: use db instead of direct xlsx

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

class LectinService:
  data: dict[str, pd.DataFrame]
  
  def __init__(self,):
    self.data = pd.read_excel(os.path.join(DATA_DIR, "galectins_id_cleaned.xlsx"), sheet_name=None) # todo: dynamic
  
  def get_lectin_info(self, id: str) -> Optional[dict]:
    '''Return available glycan info'''
    res = self.data.get(id, None)
    if res is None or res.empty: return None
    kd_col_name = res.columns[2]
    unit = kd_col_name.split(',')[1].strip()
    res = res.rename(columns={
      kd_col_name: "Kd",
      "stdev_Kd": "kderr",
      "SD": "inverr",
    })
    res["unit"] = unit

    return res.to_dict(orient="records")
    
  def get_lectins(self) -> list[str]:
    '''Return available lectins'''
    return sorted(list(self.data.keys()))
  
  
  def write_to_db(self, db: Session, df: pd.DataFrame | dict[str, pd.DataFrame], lectin: Optional[str] = None):
    '''
    Write xlsx data to database
    '''
    if isinstance(df, dict):
      for lectin, df in df.items():
        self._write_lectin_df(db, df, lectin)
    else:
      self._write_lectin_df(db, df, lectin)
  
  
  def _write_lectin_df(self, db: Session, lectin_df: pd.DataFrame, lectin: str):
    '''
    Write lectin dataframe to database
    '''
    # todo: error handling for missing columns
    # todo: standardize columns
    # todo: maybe add way to map columns in dashboard
    # todo: maybe source should be its own table with its id as the DOI ?
    for row in lectin_df.iterrows():
      row_data = row[1]
      glycan_id = row_data['GlyTouCan ID']
      glycan_name = row_data['Glycan']
      kd = row_data['Kd']
      kderr = row_data['kderr']
      inverr = row_data['inverr']
      unit = row_data['unit']
      source = row_data['Source']
      
      # get or create lectin - glycan pair in db
      pair = db.query(Pairs).filter(Pairs.lectin_id == lectin, Pairs.glycan_id == glycan_id).first()
      if pair is None:
        pair = Pairs(lectin_id=lectin, glycan_id=glycan_id)
        db.add(pair)
        db.commit()
      
      # add or update pair data in db
      pair_data = db.query(PairData).filter(PairData.pairs_id == pair.id, PairData.source == source).first()
      if pair_data is None:
        # add new pair data
        pair_data = PairData(
          pairs_id=pair.id,
          source=source,
          kd=kd,
          kderr=kderr,
          inverr=inverr,
          unit=unit
          
        )
