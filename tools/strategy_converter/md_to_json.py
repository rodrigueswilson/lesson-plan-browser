"""
Markdown to JSON converter for bilingual teaching strategies.
Uses sentinel-based parsing for robust extraction.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from utils import (
    normalize_array,
    parse_skill_weights,
    parse_bullet_list,
    extract_sentinel_section,
    sanitize_id
)


class MarkdownToJsonConverter:
    """Converts Markdown strategy documentation to JSON."""
    
    # Sentinel markers (must match json_to_md.py)
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
    
    def parse_strategy(self, markdown_text: str) -> Dict:
        """
        Parse a single strategy from Markdown.
        
        Args:
            markdown_text: Markdown text for one strategy
            
        Returns:
            Strategy dictionary
        """
        strategy = {}
        
        # Extract Strategy ID
        id_match = re.search(rf"{re.escape(self.SENTINELS['strategy_id'])}\s*(\S+)", markdown_text)
        if id_match:
            strategy['id'] = id_match.group(1).strip()
        
        # Extract Name
        name_match = re.search(rf"{re.escape(self.SENTINELS['name'])}\s*(.+?)(?:\n|$)", markdown_text)
        if name_match:
            strategy['strategy_name'] = name_match.group(1).strip()
        
        # Extract Aliases (optional)
        aliases_match = re.search(rf"{re.escape(self.SENTINELS['aliases'])}\s*(.+?)(?:\n|$)", markdown_text)
        if aliases_match:
            strategy['aliases'] = normalize_array(aliases_match.group(1))
        
        # Extract Present In (optional)
        present_match = re.search(rf"{re.escape(self.SENTINELS['present_in'])}\s*(.+?)(?:\n|$)", markdown_text)
        if present_match:
            strategy['present_in'] = normalize_array(present_match.group(1))
        
        # Extract Evidence Tier
        evidence_match = re.search(rf"{re.escape(self.SENTINELS['evidence_tier'])}\s*(.+?)(?:\n|$)", markdown_text)
        if evidence_match:
            strategy['evidence_tier'] = evidence_match.group(1).strip()
        
        # Extract High-Level Categories
        categories_match = re.search(rf"{re.escape(self.SENTINELS['categories'])}\s*(.+?)(?:\n|$)", markdown_text)
        if categories_match:
            strategy['high_level_categories'] = normalize_array(categories_match.group(1))
        
        # Extract Primary Skill
        primary_skill_match = re.search(rf"{re.escape(self.SENTINELS['primary_skill'])}\s*(\w+)", markdown_text)
        if primary_skill_match:
            strategy['primary_skill'] = primary_skill_match.group(1).strip().lower()
        
        # Extract Secondary Skills (optional)
        secondary_match = re.search(rf"{re.escape(self.SENTINELS['secondary_skills'])}\s*(.+?)(?:\n|$)", markdown_text)
        if secondary_match:
            strategy['secondary_skills'] = [s.lower() for s in normalize_array(secondary_match.group(1))]
        
        # Extract Skill Weights
        weights_match = re.search(rf"{re.escape(self.SENTINELS['skill_weights'])}\s*(.+?)(?:\n|$)", markdown_text)
        if weights_match:
            strategy['skill_weights'] = parse_skill_weights(weights_match.group(1))
        
        # Extract Delivery Modes
        delivery_match = re.search(rf"{re.escape(self.SENTINELS['delivery_modes'])}\s*(.+?)(?:\n|$)", markdown_text)
        if delivery_match:
            strategy['delivery_modes'] = normalize_array(delivery_match.group(1))
        
        # Extract L1 Modes
        l1_match = re.search(rf"{re.escape(self.SENTINELS['l1_modes'])}\s*(.+?)(?:\n|$)", markdown_text)
        if l1_match:
            strategy['l1_modes'] = normalize_array(l1_match.group(1))
        
        # Extract Integrated Framework flag
        framework_match = re.search(rf"{re.escape(self.SENTINELS['integrated_framework'])}\s*(Yes|No)", markdown_text)
        if framework_match:
            strategy['is_integrated_framework'] = framework_match.group(1) == 'Yes'
        else:
            # Fallback: infer from categories if not explicitly stated
            categories = strategy.get('high_level_categories', [])
            strategy['is_integrated_framework'] = 'Instructional Frameworks & Models' in categories
        
        # Extract Core Principle (multi-line)
        core_principle = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['core_principle'],
            self.SENTINELS['applicable_contexts']
        )
        if core_principle:
            strategy['core_principle'] = core_principle
        
        # Extract Applicable Contexts (bullet list)
        contexts_section = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['applicable_contexts'],
            self.SENTINELS['implementation_steps']
        )
        if contexts_section:
            strategy['applicable_contexts'] = parse_bullet_list(contexts_section)
        
        # Extract Implementation Steps (numbered list)
        steps_section = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['implementation_steps'],
            self.SENTINELS['primary_benefits']
        )
        if steps_section:
            strategy['implementation_steps'] = parse_bullet_list(steps_section)
        
        # Extract Primary Benefits (bullet list)
        benefits_section = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['primary_benefits'],
            self.SENTINELS['research_foundation']
        )
        if benefits_section:
            strategy['primary_benefits'] = parse_bullet_list(benefits_section)
        
        # Extract Research Foundation (optional)
        research_match = re.search(rf"{re.escape(self.SENTINELS['research_foundation'])}\s*(.+?)(?:\n|$)", markdown_text)
        if research_match:
            strategy['research_foundation'] = normalize_array(research_match.group(1))
        
        # Extract Cross-References (optional)
        cross_refs_match = re.search(rf"{re.escape(self.SENTINELS['cross_refs'])}\s*(.+?)(?:\n|$)", markdown_text)
        if cross_refs_match:
            # Could be IDs or names - sanitize to IDs
            refs = normalize_array(cross_refs_match.group(1))
            strategy['cross_refs'] = [sanitize_id(ref) for ref in refs]
        
        # Extract Definitions (v1.7+)
        definitions = {}
        
        short_def = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['definitions_short'],
            self.SENTINELS['definitions_long']
        )
        if short_def:
            definitions['short_en'] = short_def
        
        long_def = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['definitions_long'],
            self.SENTINELS['look_fors']
        )
        if long_def:
            definitions['long_en'] = long_def
        
        look_fors_section = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['look_fors'],
            self.SENTINELS['non_examples']
        )
        if look_fors_section:
            definitions['look_fors'] = parse_bullet_list(look_fors_section)
        
        non_examples_section = extract_sentinel_section(
            markdown_text,
            self.SENTINELS['non_examples'],
            '---'  # End of strategy marker
        )
        if non_examples_section:
            definitions['non_examples'] = parse_bullet_list(non_examples_section)
        
        if definitions:
            strategy['definitions'] = definitions
        
        return strategy
    
    def parse_category_file(self, markdown_text: str) -> Dict:
        """
        Parse a complete category file from Markdown.
        
        Args:
            markdown_text: Full Markdown content
            
        Returns:
            Category file dictionary with _meta and strategies
        """
        data = {'_meta': {}, 'strategies': []}
        
        # Extract metadata from header
        category_match = re.search(r'\*\*Category:\*\*\s*(.+?)(?:\n|$)', markdown_text)
        if category_match:
            data['_meta']['category'] = category_match.group(1).strip()
        
        desc_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?:\n|$)', markdown_text)
        if desc_match:
            data['_meta']['description'] = desc_match.group(1).strip()
        
        schema_match = re.search(r'\*\*Schema Version:\*\*\s*(.+?)(?:\n|$)', markdown_text)
        if schema_match:
            data['_meta']['schema_version'] = schema_match.group(1).strip()
        
        count_match = re.search(r'\*\*Strategy Count:\*\*\s*(\d+)', markdown_text)
        if count_match:
            data['_meta']['strategy_count'] = int(count_match.group(1))
        
        updated_match = re.search(r'\*\*Last Updated:\*\*\s*(.+?)(?:\n|$)', markdown_text)
        if updated_match:
            data['_meta']['last_updated'] = updated_match.group(1).strip()
        
        wida_match = re.search(r'\*\*WIDA Aligned:\*\*\s*(Yes|No)', markdown_text)
        if wida_match:
            data['_meta']['wida_aligned'] = wida_match.group(1) == 'Yes'
        
        data['_meta']['includes_definitions'] = '**Short Definition:**' in markdown_text
        
        # Split into individual strategies
        strategy_sections = re.split(r'\n---\n', markdown_text)
        
        for section in strategy_sections:
            # Check if section contains a strategy (has Strategy ID sentinel)
            if self.SENTINELS['strategy_id'] in section:
                strategy = self.parse_strategy(section)
                if strategy.get('id'):  # Only add if we got a valid ID
                    data['strategies'].append(strategy)
        
        # Update strategy count if not set
        if 'strategy_count' not in data['_meta']:
            data['_meta']['strategy_count'] = len(data['strategies'])
        
        return data
    
    def convert_file(self, input_path: str, output_path: str = None) -> Dict:
        """
        Convert Markdown file to JSON.
        
        Args:
            input_path: Path to Markdown file
            output_path: Path to output JSON file (auto-generated if None)
            
        Returns:
            Parsed data dictionary
        """
        markdown_content = Path(input_path).read_text(encoding='utf-8')
        
        # Auto-generate output path if not provided
        if output_path is None:
            input_file = Path(input_path)
            output_path = input_file.with_suffix('.json')
        
        # Determine if it's a category file or single strategy
        if '**Category:**' in markdown_content and '**Strategy Count:**' in markdown_content:
            data = self.parse_category_file(markdown_content)
        else:
            # Single strategy
            data = self.parse_strategy(markdown_content)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return data
