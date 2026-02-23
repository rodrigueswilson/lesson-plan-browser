"""
Sample lesson JSON data for JSON merger tests.
"""

from tools.test_json_merger_sample_days import build_sample_friday


def create_sample_slot(slot_number: int, subject: str, teacher_name: str) -> dict:
    """Create a sample lesson JSON for testing."""
    return {
        'slot_number': slot_number,
        'subject': subject,
        'lesson_json': {
            'metadata': {
                'week_of': '10/06-10/10',
                'grade': '3',
                'subject': subject,
                'teacher_name': teacher_name
            },
            'days': {
                'monday': {
                    'unit_lesson': f'{subject} - Unit 1 Lesson 1',
                    'objective': {
                        'content_objective': f'Students will learn {subject} concepts',
                        'student_goal': f'I will understand {subject}',
                        'wida_objective': f'Students will use language to explain {subject} concepts (ELD-SS.K-2.Explain.Reading/Writing) using visual supports and sentence frames appropriate for WIDA levels 2-5.'
                    },
                    'anticipatory_set': {
                        'original_content': 'Quick warmup activity',
                        'bilingual_bridge': 'Preview key vocabulary in Portuguese and English'
                    },
                    'tailored_instruction': {
                        'original_content': f'Teach {subject} lesson',
                        'co_teaching_model': {
                            'model_name': 'Station Teaching',
                            'rationale': 'Mixed proficiency levels',
                            'wida_context': 'Levels 2-5 distribution',
                            'phase_plan': [
                                {
                                    'phase_name': 'Practice',
                                    'minutes': 30,
                                    'bilingual_teacher_role': 'Station 1 with Levels 2-3',
                                    'primary_teacher_role': 'Station 2 with Levels 4-5'
                                }
                            ],
                            'implementation_notes': ['Prepare station materials']
                        },
                        'ell_support': [
                            {
                                'strategy_id': 'cognate_awareness',
                                'strategy_name': 'Cognate Awareness',
                                'implementation': 'Use bilingual vocabulary chart',
                                'proficiency_levels': 'Levels 2-5'
                            },
                            {
                                'strategy_id': 'sentence_frames',
                                'strategy_name': 'Sentence Frames',
                                'implementation': 'Provide sentence starters',
                                'proficiency_levels': 'Levels 2-3'
                            },
                            {
                                'strategy_id': 'visual_supports',
                                'strategy_name': 'Visual Supports',
                                'implementation': 'Use graphic organizers',
                                'proficiency_levels': 'Levels 2-4'
                            }
                        ],
                        'special_needs_support': ['Visual aids'],
                        'materials': ['Chart paper', 'Markers']
                    },
                    'misconceptions': {
                        'original_content': 'Students may confuse concepts',
                        'linguistic_note': {
                            'pattern_id': 'default',
                            'note': 'Portuguese speakers may have difficulty with this concept',
                            'prevention_tip': 'Use explicit instruction'
                        }
                    },
                    'assessment': {
                        'primary_assessment': 'Exit ticket',
                        'bilingual_overlay': {
                            'instrument': 'Written exit ticket',
                            'wida_mapping': 'Explain + ELD-SS.K-2.Writing + Levels 2-5',
                            'supports_by_level': {
                                'levels_1_2': 'Sentence frames and word bank',
                                'levels_3_4': 'Sentence starters',
                                'levels_5_6': 'Open response'
                            },
                            'scoring_lens': 'Focus on content understanding',
                            'constraints_honored': 'No new materials'
                        }
                    },
                    'homework': {
                        'original_content': 'Practice worksheet',
                        'family_connection': 'Discuss with family in L1'
                    }
                },
                'tuesday': {
                    'unit_lesson': f'{subject} - Unit 1 Lesson 2',
                    'objective': {
                        'content_objective': f'Students will apply {subject} concepts',
                        'student_goal': f'I will practice {subject}',
                        'wida_objective': f'Students will use language to apply {subject} concepts (ELD-SS.K-2.Explain.Reading/Writing) using visual supports appropriate for WIDA levels 2-5.'
                    },
                    'anticipatory_set': {
                        'original_content': 'Review previous lesson',
                        'bilingual_bridge': 'Connect to L1 knowledge'
                    },
                    'tailored_instruction': {
                        'original_content': f'Practice {subject} skills',
                        'co_teaching_model': {
                            'model_name': 'Parallel Teaching',
                            'rationale': 'Two groups for differentiation',
                            'wida_context': 'Mixed proficiency',
                            'phase_plan': [
                                {
                                    'phase_name': 'Practice',
                                    'minutes': 35,
                                    'bilingual_teacher_role': 'Group A - Intensive support',
                                    'primary_teacher_role': 'Group B - Independent practice'
                                }
                            ],
                            'implementation_notes': ['Prepare two sets of materials']
                        },
                        'ell_support': [
                            {
                                'strategy_id': 'graphic_organizers',
                                'strategy_name': 'Graphic Organizers',
                                'implementation': 'Use concept maps',
                                'proficiency_levels': 'Levels 2-4'
                            },
                            {
                                'strategy_id': 'peer_support',
                                'strategy_name': 'Peer Support',
                                'implementation': 'Partner work',
                                'proficiency_levels': 'Levels 2-5'
                            },
                            {
                                'strategy_id': 'scaffolded_questions',
                                'strategy_name': 'Scaffolded Questions',
                                'implementation': 'Tiered questioning',
                                'proficiency_levels': 'Levels 2-5'
                            }
                        ],
                        'special_needs_support': ['Extra time'],
                        'materials': ['Worksheets', 'Manipulatives']
                    },
                    'misconceptions': {
                        'original_content': 'Common errors in application',
                        'linguistic_note': {
                            'pattern_id': 'default',
                            'note': 'Language interference may occur',
                            'prevention_tip': 'Model correct usage'
                        }
                    },
                    'assessment': {
                        'primary_assessment': 'Practice problems',
                        'bilingual_overlay': {
                            'instrument': 'Written practice',
                            'wida_mapping': 'Explain + ELD-SS.K-2.Writing + Levels 2-5',
                            'supports_by_level': {
                                'levels_1_2': 'Visual supports and frames',
                                'levels_3_4': 'Partial scaffolds',
                                'levels_5_6': 'Minimal support'
                            },
                            'scoring_lens': 'Focus on process',
                            'constraints_honored': 'Uses existing materials'
                        }
                    },
                    'homework': {
                        'original_content': 'Review notes',
                        'family_connection': 'Share learning with family'
                    }
                },
                'wednesday': {
                    'unit_lesson': f'{subject} - Unit 1 Lesson 3',
                    'objective': {
                        'content_objective': f'Students will master {subject} skills',
                        'student_goal': f'I will demonstrate {subject} mastery',
                        'wida_objective': f'Students will use language to demonstrate {subject} mastery (ELD-SS.K-2.Explain.Reading/Writing) appropriate for WIDA levels 2-5.'
                    },
                    'anticipatory_set': {
                        'original_content': 'Quick check',
                        'bilingual_bridge': 'Activate prior knowledge'
                    },
                    'tailored_instruction': {
                        'original_content': f'Apply {subject} concepts',
                        'co_teaching_model': {
                            'model_name': 'Team Teaching',
                            'rationale': 'Collaborative instruction',
                            'wida_context': 'All levels together',
                            'phase_plan': [
                                {
                                    'phase_name': 'Input',
                                    'minutes': 40,
                                    'bilingual_teacher_role': 'Co-present with language support',
                                    'primary_teacher_role': 'Co-present with content focus'
                                }
                            ],
                            'implementation_notes': ['Coordinate presentation']
                        },
                        'ell_support': [
                            {
                                'strategy_id': 'modeling',
                                'strategy_name': 'Modeling',
                                'implementation': 'Demonstrate process',
                                'proficiency_levels': 'Levels 2-5'
                            },
                            {
                                'strategy_id': 'think_aloud',
                                'strategy_name': 'Think Aloud',
                                'implementation': 'Verbalize thinking',
                                'proficiency_levels': 'Levels 3-5'
                            },
                            {
                                'strategy_id': 'chunking',
                                'strategy_name': 'Chunking',
                                'implementation': 'Break into steps',
                                'proficiency_levels': 'Levels 2-4'
                            }
                        ],
                        'special_needs_support': ['Step-by-step guide'],
                        'materials': ['Examples', 'Templates']
                    },
                    'misconceptions': {
                        'original_content': 'Address common errors',
                        'linguistic_note': {
                            'pattern_id': 'default',
                            'note': 'Clarify language patterns',
                            'prevention_tip': 'Provide explicit examples'
                        }
                    },
                    'assessment': {
                        'primary_assessment': 'Quiz',
                        'bilingual_overlay': {
                            'instrument': 'Written quiz',
                            'wida_mapping': 'Explain + ELD-SS.K-2.Writing + Levels 2-5',
                            'supports_by_level': {
                                'levels_1_2': 'Modified format',
                                'levels_3_4': 'Standard with supports',
                                'levels_5_6': 'Standard format'
                            },
                            'scoring_lens': 'Content mastery',
                            'constraints_honored': 'Same quiz format'
                        }
                    },
                    'homework': {
                        'original_content': 'Study for test',
                        'family_connection': 'Review with family'
                    }
                },
                'thursday': {
                    'unit_lesson': f'{subject} - Unit 1 Lesson 4',
                    'objective': {
                        'content_objective': f'Students will extend {subject} knowledge',
                        'student_goal': f'I will explore {subject} further',
                        'wida_objective': f'Students will use language to extend {subject} knowledge (ELD-SS.K-2.Explain.Reading/Writing) appropriate for WIDA levels 2-5.'
                    },
                    'anticipatory_set': {
                        'original_content': 'Engage with question',
                        'bilingual_bridge': 'Connect to experience'
                    },
                    'tailored_instruction': {
                        'original_content': f'Extend {subject} learning',
                        'co_teaching_model': {
                            'model_name': 'Alternative Teaching',
                            'rationale': 'Small group intervention',
                            'wida_context': 'Targeted support needed',
                            'phase_plan': [
                                {
                                    'phase_name': 'Practice',
                                    'minutes': 35,
                                    'bilingual_teacher_role': 'Small group intensive support',
                                    'primary_teacher_role': 'Large group instruction'
                                }
                            ],
                            'implementation_notes': ['Identify small group students']
                        },
                        'ell_support': [
                            {
                                'strategy_id': 'realia',
                                'strategy_name': 'Realia',
                                'implementation': 'Use real objects',
                                'proficiency_levels': 'Levels 2-4'
                            },
                            {
                                'strategy_id': 'gestures',
                                'strategy_name': 'Gestures',
                                'implementation': 'Use TPR',
                                'proficiency_levels': 'Levels 2-3'
                            },
                            {
                                'strategy_id': 'repetition',
                                'strategy_name': 'Repetition',
                                'implementation': 'Repeat key concepts',
                                'proficiency_levels': 'Levels 2-4'
                            }
                        ],
                        'special_needs_support': ['Hands-on materials'],
                        'materials': ['Concrete objects', 'Pictures']
                    },
                    'misconceptions': {
                        'original_content': 'Clarify misunderstandings',
                        'linguistic_note': {
                            'pattern_id': 'default',
                            'note': 'Address language barriers',
                            'prevention_tip': 'Use multiple modalities'
                        }
                    },
                    'assessment': {
                        'primary_assessment': 'Project',
                        'bilingual_overlay': {
                            'instrument': 'Project presentation',
                            'wida_mapping': 'Explain + ELD-SS.K-2.Speaking + Levels 2-5',
                            'supports_by_level': {
                                'levels_1_2': 'Visual presentation with minimal text',
                                'levels_3_4': 'Presentation with notes',
                                'levels_5_6': 'Full presentation'
                            },
                            'scoring_lens': 'Content and communication',
                            'constraints_honored': 'Same project requirements'
                        }
                    },
                    'homework': {
                        'original_content': 'Work on project',
                        'family_connection': 'Get family input'
                    }
                },
                'friday': build_sample_friday(subject)
            }
        }
    }
