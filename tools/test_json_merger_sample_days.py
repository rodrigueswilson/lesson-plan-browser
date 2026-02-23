"""Sample lesson days data for JSON merger tests. Builds Friday (and can hold other day builders)."""


def build_sample_friday(subject: str) -> dict:
    """Build the Friday day dict for create_sample_slot."""
    return {
        'unit_lesson': f'{subject} - Unit 1 Review',
        'objective': {
            'content_objective': f'Students will review {subject} unit',
            'student_goal': f'I will review {subject} concepts',
            'wida_objective': f'Students will use language to review {subject} concepts (ELD-SS.K-2.Explain.Reading/Writing) appropriate for WIDA levels 2-5.'
        },
        'anticipatory_set': {
            'original_content': 'Review week',
            'bilingual_bridge': 'Summarize in L1 and L2'
        },
        'tailored_instruction': {
            'original_content': f'Review {subject} unit',
            'co_teaching_model': {
                'model_name': 'Station Teaching',
                'rationale': 'Review stations',
                'wida_context': 'Differentiated review',
                'phase_plan': [
                    {
                        'phase_name': 'Review',
                        'minutes': 40,
                        'bilingual_teacher_role': 'Language review station',
                        'primary_teacher_role': 'Content review station'
                    }
                ],
                'implementation_notes': ['Prepare review materials']
            },
            'ell_support': [
                {
                    'strategy_id': 'summarizing',
                    'strategy_name': 'Summarizing',
                    'implementation': 'Create summary charts',
                    'proficiency_levels': 'Levels 3-5'
                },
                {
                    'strategy_id': 'review_games',
                    'strategy_name': 'Review Games',
                    'implementation': 'Interactive review',
                    'proficiency_levels': 'Levels 2-5'
                },
                {
                    'strategy_id': 'self_assessment',
                    'strategy_name': 'Self Assessment',
                    'implementation': 'Reflection checklist',
                    'proficiency_levels': 'Levels 3-5'
                }
            ],
            'special_needs_support': ['Review guide'],
            'materials': ['Review sheets', 'Games']
        },
        'misconceptions': {
            'original_content': 'Final clarifications',
            'linguistic_note': {
                'pattern_id': 'default',
                'note': 'Review language points',
                'prevention_tip': 'Reinforce correct usage'
            }
        },
        'assessment': {
            'primary_assessment': 'Unit test',
            'bilingual_overlay': {
                'instrument': 'Written test',
                'wida_mapping': 'Explain + ELD-SS.K-2.Writing + Levels 2-5',
                'supports_by_level': {
                    'levels_1_2': 'Modified test with visuals',
                    'levels_3_4': 'Standard test with supports',
                    'levels_5_6': 'Standard test'
                },
                'scoring_lens': 'Unit mastery',
                'constraints_honored': 'Same test content'
            }
        },
        'homework': {
            'original_content': 'Enjoy weekend',
            'family_connection': 'Share unit learning with family'
        }
    }
