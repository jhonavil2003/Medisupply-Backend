from src.entities.visit_status import VisitStatus


class TestVisitStatusEntity:
    """Test cases for VisitStatus enum"""
    
    def test_visit_status_values(self):
        """Test that all expected status values exist."""
        assert VisitStatus.PROGRAMADA.value == "PROGRAMADA"
        assert VisitStatus.COMPLETADA.value == "COMPLETADA"
        assert VisitStatus.ELIMINADA.value == "ELIMINADA"
    
    def test_visit_status_string_representation(self):
        """Test string representation of status values."""
        assert str(VisitStatus.PROGRAMADA) == "PROGRAMADA"
        assert str(VisitStatus.COMPLETADA) == "COMPLETADA"
        assert str(VisitStatus.ELIMINADA) == "ELIMINADA"
    
    def test_visit_status_from_string_exact_match(self):
        """Test creating status from exact string match."""
        assert VisitStatus.from_string("PROGRAMADA") == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string("COMPLETADA") == VisitStatus.COMPLETADA
        assert VisitStatus.from_string("ELIMINADA") == VisitStatus.ELIMINADA
    
    def test_visit_status_from_string_lowercase(self):
        """Test creating status from lowercase strings."""
        assert VisitStatus.from_string("programada") == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string("completada") == VisitStatus.COMPLETADA
        assert VisitStatus.from_string("eliminada") == VisitStatus.ELIMINADA
    
    def test_visit_status_from_string_backward_compatibility(self):
        """Test backward compatibility with old status names."""
        # SCHEDULED -> PROGRAMADA
        assert VisitStatus.from_string("SCHEDULED") == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string("scheduled") == VisitStatus.PROGRAMADA
        
        # COMPLETED -> COMPLETADA
        assert VisitStatus.from_string("COMPLETED") == VisitStatus.COMPLETADA
        assert VisitStatus.from_string("completed") == VisitStatus.COMPLETADA
        
        # DELETED/CANCELLED -> ELIMINADA
        assert VisitStatus.from_string("DELETED") == VisitStatus.ELIMINADA
        assert VisitStatus.from_string("deleted") == VisitStatus.ELIMINADA
        assert VisitStatus.from_string("CANCELLED") == VisitStatus.ELIMINADA
        assert VisitStatus.from_string("cancelled") == VisitStatus.ELIMINADA
    
    def test_visit_status_from_string_invalid(self):
        """Test handling of invalid status strings."""
        # Invalid strings should return PROGRAMADA as default
        assert VisitStatus.from_string("INVALID") == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string("") == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string(None) == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string("random_text") == VisitStatus.PROGRAMADA
    
    def test_visit_status_from_string_exception_handling(self):
        """Test that exceptions are handled gracefully."""
        # Test with different data types that might cause exceptions
        assert VisitStatus.from_string(123) == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string([]) == VisitStatus.PROGRAMADA
        assert VisitStatus.from_string({}) == VisitStatus.PROGRAMADA
    
    def test_visit_status_equality(self):
        """Test status equality comparisons."""
        status1 = VisitStatus.PROGRAMADA
        status2 = VisitStatus.from_string("PROGRAMADA")
        status3 = VisitStatus.from_string("SCHEDULED")  # Should map to PROGRAMADA
        
        assert status1 == status2
        assert status1 == status3
        assert status2 == status3
        
        assert status1 != VisitStatus.COMPLETADA
        assert status1 != VisitStatus.ELIMINADA
    
    def test_visit_status_in_collections(self):
        """Test using status values in collections."""
        all_statuses = [VisitStatus.PROGRAMADA, VisitStatus.COMPLETADA, VisitStatus.ELIMINADA]
        
        assert VisitStatus.PROGRAMADA in all_statuses
        assert VisitStatus.COMPLETADA in all_statuses
        assert VisitStatus.ELIMINADA in all_statuses
        
        # Test set operations
        status_set = {VisitStatus.PROGRAMADA, VisitStatus.COMPLETADA}
        assert len(status_set) == 2
        assert VisitStatus.PROGRAMADA in status_set
        assert VisitStatus.ELIMINADA not in status_set
    
    def test_visit_status_dict_keys(self):
        """Test using status as dictionary keys."""
        status_dict = {
            VisitStatus.PROGRAMADA: "yellow",
            VisitStatus.COMPLETADA: "green", 
            VisitStatus.ELIMINADA: "red"
        }
        
        assert status_dict[VisitStatus.PROGRAMADA] == "yellow"
        assert status_dict[VisitStatus.COMPLETADA] == "green"
        assert status_dict[VisitStatus.ELIMINADA] == "red"
    
    def test_visit_status_serialization(self):
        """Test status serialization for JSON."""
        # Test that .value gives proper string for JSON
        assert VisitStatus.PROGRAMADA.value == "PROGRAMADA"
        assert VisitStatus.COMPLETADA.value == "COMPLETADA"
        assert VisitStatus.ELIMINADA.value == "ELIMINADA"
        
        # Test that we can reconstruct from serialized value
        serialized = VisitStatus.PROGRAMADA.value
        reconstructed = VisitStatus.from_string(serialized)
        assert reconstructed == VisitStatus.PROGRAMADA
    
    def test_visit_status_all_enum_members(self):
        """Test that we can iterate over all enum members."""
        all_members = list(VisitStatus)
        assert len(all_members) == 3
        assert VisitStatus.PROGRAMADA in all_members
        assert VisitStatus.COMPLETADA in all_members
        assert VisitStatus.ELIMINADA in all_members
    
    def test_visit_status_name_property(self):
        """Test the name property of enum members."""
        assert VisitStatus.PROGRAMADA.name == "PROGRAMADA"
        assert VisitStatus.COMPLETADA.name == "COMPLETADA" 
        assert VisitStatus.ELIMINADA.name == "ELIMINADA"