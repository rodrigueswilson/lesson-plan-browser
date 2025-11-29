"""
JSON to Markdown converter for bilingual teaching strategies.
Uses sentinel headings for robust round-trip conversion.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from utils import (
    format_skill_weights,
    format_list_as_bullets,
    format_field_value
)


class JsonToMarkdownConverter:
    """Converts strategy JSON to human-readable Markdown."""
    
    # Sentinel markers for each section
    SENTINELS = {
        'strategy_id': '### Strategy ID:',
        'name': '**Name:**',
        'aliases': '**Aliases:**',
        'present_in': '**Present In:**',
        'evidence_tier': '**Evidence Tier:**',
        'categories': '**High-Level Categories:**',
        'primary_skill': '**Primary Skill:**',
        'secondary_skills': '**Secondary Skills:**',
        'skill_weights': '**Skill Weights:**',
        'delivery_modes': '**Delivery Mode:**',
        'l1_modes': '**L1 Mode:**',
        'integrated_framework': '**Integrated Framework:**',
        'core_principle': '**Core Principle:**',
        'applicable_contexts': '**Applicable Contexts:**',
        'implementation_steps': '**Implementation Steps:**',
        'primary_benefits': '**Primary Benefits:**',
        'research_foundation': '**Research Foundation:**',
        'cross_refs': '**Cross-References:**',
        'definitions_short': '**Short Definition:**',
        'definitions_long': '**Long Definition:**',
        'look_fors': '**Look-Fors (Observable Indicators):**',
        'non_examples': '**Non-Examples (Avoid):**'
    }
    
    def __init__(self):
        """Initialize converter."""
        pass
    
    def convert_strategy(self, strategy: Dict, include_definitions: bool = True) -> str:
        """
        Convert a single strategy to Markdown.
        
        Args:
            strategy: Strategy dictionary
            include_definitions: Whether to include definitions section
            
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Strategy ID (heading)
        lines.append(f"{self.SENTINELS['strategy_id']} {strategy['id']}")
        lines.append("")
        
        # Name
        lines.append(f"{self.SENTINELS['name']} {strategy['strategy_name']}")
        lines.append("")
        
        # Aliases (optional)
        if strategy.get('aliases'):
            aliases_str = ', '.join(strategy['aliases'])
            lines.append(f"{self.SENTINELS['aliases']} {aliases_str}")
            lines.append("")
        
        # Present In (optional)
        if strategy.get('present_in'):
            present_str = ', '.join(strategy['present_in'])
            lines.append(f"{self.SENTINELS['present_in']} {present_str}")
            lines.append("")
        
        # Evidence Tier
        lines.append(f"{self.SENTINELS['evidence_tier']} {strategy['evidence_tier']}")
        lines.append("")
        
        # High-Level Categories
        categories_str = ', '.join(strategy['high_level_categories'])
        lines.append(f"{self.SENTINELS['categories']} {categories_str}")
        lines.append("")
        
        # Primary Skill
        lines.append(f"{self.SENTINELS['primary_skill']} {strategy['primary_skill']}")
        lines.append("")
        
        # Secondary Skills (optional)
        if strategy.get('secondary_skills'):
            secondary_str = ', '.join(strategy['secondary_skills'])
            lines.append(f"{self.SENTINELS['secondary_skills']} {secondary_str}")
            lines.append("")
        
        # Skill Weights
        weights_str = format_skill_weights(strategy['skill_weights'])
        lines.append(f"{self.SENTINELS['skill_weights']} {weights_str}")
        lines.append("")
        
        # Delivery Modes
        delivery_str = ', '.join(strategy['delivery_modes'])
        lines.append(f"{self.SENTINELS['delivery_modes']} {delivery_str}")
        lines.append("")
        
        # L1 Modes
        l1_str = ', '.join(strategy['l1_modes'])
        lines.append(f"{self.SENTINELS['l1_modes']} {l1_str}")
        lines.append("")
        
        # Integrated Framework flag
        is_framework = "Yes" if strategy.get('is_integrated_framework', False) else "No"
        lines.append(f"**Integrated Framework:** {is_framework}")
        lines.append("")
        
        # Core Principle
        lines.append(f"{self.SENTINELS['core_principle']}")
        lines.append(strategy['core_principle'])
        lines.append("")
        
        # Applicable Contexts
        lines.append(f"{self.SENTINELS['applicable_contexts']}")
        for context in strategy['applicable_contexts']:
            lines.append(f"- {context}")
        lines.append("")
        
        # Implementation Steps
        lines.append(f"{self.SENTINELS['implementation_steps']}")
        for idx, step in enumerate(strategy['implementation_steps'], 1):
            lines.append(f"{idx}. {step}")
        lines.append("")
        
        # Primary Benefits
        lines.append(f"{self.SENTINELS['primary_benefits']}")
        for benefit in strategy['primary_benefits']:
            lines.append(f"- {benefit}")
        lines.append("")
        
        # Research Foundation (optional)
        if strategy.get('research_foundation'):
            research_str = ', '.join(strategy['research_foundation'])
            lines.append(f"{self.SENTINELS['research_foundation']} {research_str}")
            lines.append("")
        
        # Cross-References (optional)
        if strategy.get('cross_refs'):
            # Convert IDs to readable names if possible (for now, just show IDs)
            refs_str = ', '.join(strategy['cross_refs'])
            lines.append(f"{self.SENTINELS['cross_refs']} {refs_str}")
            lines.append("")
        
        # Definitions section (v1.7+)
        if include_definitions and strategy.get('definitions'):
            defs = strategy['definitions']
            
            if defs.get('short_en'):
                lines.append(f"{self.SENTINELS['definitions_short']}")
                lines.append(defs['short_en'])
                lines.append("")
            
            if defs.get('long_en'):
                lines.append(f"{self.SENTINELS['definitions_long']}")
                lines.append(defs['long_en'])
                lines.append("")
            
            if defs.get('look_fors'):
                lines.append(f"{self.SENTINELS['look_fors']}")
                for item in defs['look_fors']:
                    lines.append(f"- {item}")
                lines.append("")
            
            if defs.get('non_examples'):
                lines.append(f"{self.SENTINELS['non_examples']}")
                for item in defs['non_examples']:
                    lines.append(f"- {item}")
                lines.append("")
        
        # Add separator
        lines.append("---")
        lines.append("")
        
        return '\n'.join(lines)
    
    def convert_category_file(self, data: Dict, output_path: str = None) -> str:
        """
        Convert a complete category file to Markdown.
        
        Args:
            data: Category file dictionary with _meta and strategies
            output_path: Optional path to write output
            
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Header
        meta = data.get('_meta', {})
        category_name = meta.get('category', 'Unknown Category').replace('_', ' ').title()
        
        lines.append(f"# {category_name} Strategies")
        lines.append("")
        lines.append(f"**Category:** {meta.get('category', 'unknown')}")
        lines.append(f"**Description:** {meta.get('description', '')}")
        lines.append(f"**Schema Version:** {meta.get('schema_version', 'unknown')}")
        lines.append(f"**Strategy Count:** {meta.get('strategy_count', 0)}")
        lines.append(f"**Last Updated:** {meta.get('last_updated', 'unknown')}")
        lines.append(f"**WIDA Aligned:** {'Yes' if meta.get('wida_aligned') else 'No'}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Convert each strategy
        for strategy in data.get('strategies', []):
            strategy_md = self.convert_strategy(
                strategy,
                include_definitions=meta.get('includes_definitions', True)
            )
            lines.append(strategy_md)
        
        markdown_content = '\n'.join(lines)
        
        # Write to file if path provided
        if output_path:
            Path(output_path).write_text(markdown_content, encoding='utf-8')
        
        return markdown_content
    
    def convert_file(self, input_path: str, output_path: str = None) -> str:
        """
        Convert JSON file to Markdown.
        
        Args:
            input_path: Path to JSON file
            output_path: Path to output MD file (auto-generated if None)
            
        Returns:
            Markdown content
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Auto-generate output path if not provided
        if output_path is None:
            input_file = Path(input_path)
            output_path = input_file.with_suffix('.md')
        
        # Determine if it's a category file or single strategy
        if '_meta' in data and 'strategies' in data:
            return self.convert_category_file(data, output_path)
        else:
            # Single strategy
            markdown_content = self.convert_strategy(data)
            Path(output_path).write_text(markdown_content, encoding='utf-8')
            return markdown_content
