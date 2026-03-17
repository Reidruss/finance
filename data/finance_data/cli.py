import click
from pathlib import Path
from finance_data.parsers import GenericCsvParser
from finance_data.writer import ParquetStore
import sys

@click.command()
@click.option('--input', '-i', type=click.Path(exists=True, dir_okay=False), required=True, help='Path to input CSV file')
@click.option('--output', '-o', type=click.Path(), required=True, help='Path to output storage directory')
@click.option('--type', '-t', type=click.Choice(['trades', 'l2']), required=True, help='Type of data to process')
@click.option('--symbol', '-s', required=True, help='Symbol representing the data (e.g. BTC-USD)')
def main(input, output, type, symbol):
    """Ingest market data and store it in partitioned parquet format."""
    
    click.echo(f"Starting ingestion for {symbol} - {type} from {input}")
    
    parser = GenericCsvParser(symbol=symbol)
    store = ParquetStore(output)
    
    try:
        if type == 'trades':
            lf = parser.parse_trades(str(input))
            store.write_trades(lf)
            click.echo("Successfully wrote trades.")
        elif type == 'l2':
            lf = parser.parse_l2_updates(str(input))
            store.write_l2_updates(lf)
            click.echo("Successfully wrote L2 updates.")
            
    except Exception as e:
        click.echo(f"Error processing file: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
