import xml.etree.ElementTree as ET

def parse_dividend_xml(xml_data):
    """
    Estrae dividendi e informazioni correlate dall'XML IBKR.
    Ritorna un dizionario con i valori estratti.
    """

    root = ET.fromstring(xml_data)

    result = {
        "last_dividend": None,
        "projected_dividend": None,
        "ex_date": None,
        "pay_date": None,
        "yield": None
    }

    # --- 1. Ultimo dividendo pagato (TTMDIVSHR) ---
    for ratio in root.findall(".//Ratio"):
        if ratio.attrib.get("FieldName") == "TTMDIVSHR":
            result["last_dividend"] = float(ratio.text)
        if ratio.attrib.get("FieldName") == "NPRICE":
            price = float(ratio.text)
            result["price"] = price

    # --- 2. Dividendo stimato (ProjDPS) ---
    proj = root.find(".//Ratio[@FieldName='ProjDPS']/Value")
    if proj is not None:
        result["projected_dividend"] = float(proj.text)

    # --- 3. Ex‑Dividend Date ---
    ex_date = root.find(".//ExDate")
    if ex_date is not None:
        result["ex_date"] = ex_date.text

    # --- 4. Pay Date ---
    pay_date = root.find(".//PayDate")
    if pay_date is not None:
        result["pay_date"] = pay_date.text

    # --- 5. Dividend Yield (calcolato) ---
    if result["last_dividend"] and "price" in result:
        result["yield"] = result["last_dividend"] / result["price"]

    return result
