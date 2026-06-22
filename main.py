from clean_data import run_cleaning
from train_model import train_models
from visualize import create_visualizations
from sentiment_analysis import analyze_sentiment


if __name__ == "__main__":
    # Run sentiment first so its signals can be fused into the ML dataset
    try:
        sentiment_outputs = analyze_sentiment()
    except Exception as e:
        sentiment_outputs = {"rows": 0, "message": str(e)}

    cleaning_outputs = run_cleaning()
    training_outputs = train_models(data_path=cleaning_outputs["ml_ready"])

    visual_outputs = create_visualizations()

    print(f"Cleaned datasets written to: {cleaning_outputs['output_dir']}")
    print(f"ML-ready dataset: {cleaning_outputs['ml_ready']}")
    print(f"Quality report: {cleaning_outputs['quality_report']}")
    print(f"Sentiment text template: {cleaning_outputs['sentiment_template']}")
    print(f"Sentiment scored: {sentiment_outputs.get('rows', 0)} (method: {sentiment_outputs.get('method', 'n/a')})")
    print(f"Training metrics: {training_outputs['metrics']}")
    print(f"Fitted predictions: {training_outputs['predictions']}")
    print(f"Best model metadata: {training_outputs['best_models']}")
    print(f"Training report: {training_outputs['report']}")
    print(f"Saved models: {training_outputs['model_dir']}")
    print(f"Charts: {visual_outputs['figure_dir']}")
    print(f"Visual report: {visual_outputs['report']}")
