import yaml

class problem(object):
    """
    description - string?
    mesh - třída?
    flow_equation - třída -> !Flow_Darcy_MH
        non_linear_solver - ??? - třída?
            linear_solver - třída -> !Petsc
                a_tol - float? ( číslo: 1.0e-07 )
        input_fields - slovník ??? - jak udělat přes pole?
            - region - string
              conductivity - float? ( číslo: 1.0e-15 )
            - region - string?
              bc_type - string?
              bc_pressure - int?float
        output - ??? -> třída?
            fields - list
                - pressure_p0
                - pressure_p1
                - velocity_p0
        output_stream - ??? -> třída
            file - string?
            format - třída -> !vtk
                variant: string
    solute_equation - třída -> !Coupling_OperatorSplitting
        transport - třída -> !Solute_Advection_FV
            input_fields - ??? -> třída? složené pole dvou polí? možné dynamicky
                region - string
                init_conc - list
                porosity - float
                region - string
                bc_conc - float
        substances: - list
        output_stream - ??? -> třída
            file - string
            format - třída -> !vtk
                variant: string
            times - ??? - třída -> složené pole?
                step - float
        time - ??? -> třída?? stačí pole???
            end_time - float nebo datetime?
        reaction_term - třída -> !DualPorosity
            input_fields - ??? - třída
                region - string
                diffusion_rate_immobile - list
                porosity_immobile - float
                init_conc_immobile - list
            scheme_tolerance - float
            reaction_tolerance - float
            reaction_mobile - třída -> !SorptionMobile
                solvent_density - float
                substances - list -> jde o kotvu
                solubility - list -> jde o kotvu
                input_fields - ??? - třída -> jde o kotvu
                    region - string
                    rock_density - float
                    sorption_type - string
                    distribution_coefficient - float
                    isotherm_other - float
                reaction_liquid - třída -> !FirstOrderReaction -> jde o kotvu
                    reactions - ??? - třída?
                        reactants - string
                        preaction_rate - float
                        products - string
            reaction_immobile - třída -> !SorptionImmobile
                solvent_density - float
                substances - list -> využívá kotvu
                solubility - list -> využívá kotvu
                input_fields - ??? - třída -> využívá kotvu
                reaction_liquid - třída -> !FirstOrderReaction -> využívá kotvu
    balance - ??? - třída
        cumulative - bool?

                bacha na ty region nahoře
    """